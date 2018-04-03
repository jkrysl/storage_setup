# Copyright (C) 2018 Red Hat, Inc.
# This file is based on copy from https://gitlab.com/rh-kernel-stqe/python-stqe/edit/master/stqe/host/fmf_tools.py

"""fmf_tools.py: Module to manipulate FMF."""

import fmf.utils
import os
import sys
from fmf import Tree
from random import shuffle

_INSTALL_SCRIPT = """#!/usr/bin/python
import subprocess

subprocess.Popen("yum install -y %s" % pack)
"""


def get_path():
    return os.getcwd()


def get_dir_from_name(name):
    if not os.path.isdir(get_path() + "/tests/" + name):
        return "/".join(name.split("/")[:-1])
    return name


def get_tree(name=""):
    path = get_path() + "/" + get_dir_from_name(name)
    tree = Tree(path)
    tree.grow(path)
    return tree


def get_tests_path(name):
    return get_path() + "/tests/" + get_dir_from_name(name)


def get_test_name(tree):
    return "/".join(tree.name.split("/")[1:-1]) + "/" + tree.get('test')


def remove_redundant(leaf):
    for att in ['tester', 'description', 'setup', 'active', 'requires_install', 'requires_cleanup', 'requires_setup',
                'component']:
        try:
            leaf.pop(att)
        except KeyError:
            pass
    return leaf


def get_tests(name=None, filter=list(""), os_env_asterix=None):
    test_path = get_path() + "/tests/"
    if not os.path.isdir(get_path() + "/tests/" + name):
        test_path += "/".join(name.split("/")[:-1])
    else:
        test_path += name

    # Need to get the whole tree because of inheritance
    tree = get_tree()
    config = {
        "install": [],
        "tests": [],
        "setups": []
    }

    for i in tree.climb():
        leaf = i.get()
        print leaf

        # do not run deactivated tests
        if 'active' in leaf and not leaf['active']:
            continue

        # no file associated with this metadata, skipping
        if 'test' not in leaf:
            continue
        # replace test value with path from stqe/tests
        leaf['test'] = get_test_name(i)

        test_name = i.name.split("/")
        if len(test_name) > 1:
            leaf['name'] = "/".join(test_name[1:])
        else:
            leaf['name'] = i.name

        # do not run setups / cleanups, they are ran by specifying 'requires_setup' / 'requires_cleanup' in test meta
        # add them to "setups" so we can locate tham later without running though the tree again
        if 'setup' in leaf and leaf['setup']:
            config["setups"].append(leaf)
            config, leaf = insert_install(config, leaf)
            continue

        if name is not None and name not in i.show(brief=True):
            continue

        # apply filter
        if not all([fmf_filter(filter=f, node=dict(leaf)) for f in filter]):
            continue

        config, leaf = insert_install(config, leaf)

        if 'requires_setup' not in leaf:
            # this test does not require setup
            is_in_tests = _is_test_in_tests(leaf, config['tests'])
            if isinstance(is_in_tests, bool) and not is_in_tests:
                config['tests'].append(leaf)
            elif isinstance(is_in_tests, int):
                # replace test if it is greater tier
                config['tests'][is_in_tests] = leaf
            test_position = _get_test_position(leaf['test'], config['tests'])
            try:
                if test_position is not None and leaf['tier'] > config['tests'][test_position]['tier']:
                    # replacing tier with higher one
                    config['tests'][test_position] = leaf
            except KeyError:
                pass
            if not _is_test_in_tests(leaf['test'], config['tests']):
                # test is not in yet
                config['tests'].append(leaf)
        else:
            requires_setup = replace_require_setup(leaf, os_env_asterix)
            config = insert_test(config, requires_setup, leaf)
    return config


def insert_install(tests, leaf):
    # write install test file for each package and adds them to the beginning of tests
    if 'requires_install' not in leaf:
        return tests, leaf
    requires_install = leaf.pop('requires_install')
    if not isinstance(requires_install, list):
        requires_install = [requires_install]
    for to_install in requires_install:
        inst_file = "install_%s.py" % to_install
        if not os.path.isfile(get_path() + "/tests/" + inst_file):
            with open(get_path() + "/" + inst_file, 'w') as f:
                script = _INSTALL_SCRIPT.split('pack')
                script.insert(1, "'%s'" % to_install)
                # write the inst file itself
                f.writelines("".join(script))
                # write inst file to config to be ran
        inst = {'test': inst_file, 'name': inst_file}
        if inst not in tests['install']:
            tests['install'].insert(0, inst)
    return tests, leaf


def _get_test_position(test, tests):
    for i, t in enumerate(tests):
        if test == t['test']:
            return i
    return None


def _is_test_in_tests(test, tests):
    for i, t in enumerate(tests):
        if test == t['test']:
            return True
    return False


def replace_require_setup(leaf, os_env=None):
    require_setup = leaf.pop('requires_setup')
    # check if the setup requirement needs to be altered (contains "*")
    if not isinstance(require_setup, list):
        require_setup = [require_setup]
    req = ""
    for requirement in require_setup:
        if "*" in requirement:
            if os_env is None:
                print("FAIL: Set '%s' env to specify setup type for tests." % os_env)
                exit(1)
            env = os_env.split()
            # replace '*' with the correct device type and adds the rest setup functions
            req = ""
            for i, x in enumerate(env):
                if i == 0:
                    req += x.join(requirement.split("*"))
                else:
                    req += " " + x
        else:
            req += requirement
        req += " "
    return req


def insert_test(dictionary, name, test):
    name = [x.strip() for x in name.split()]
    if len(name) == 1:
        this_name = name[0]
        name = None
    else:
        this_name = name.pop(0)
        name = " ".join(name)
    if this_name not in dictionary:
        dictionary[this_name] = dict()
        dictionary[this_name]['tests'] = []
    for key in dictionary:
        if isinstance(dictionary[key], dict) and name is not None and key == this_name:
            insert_test(dictionary[key], name, test)
        if name is None and key == this_name:
            test_position = _get_test_position(test['test'], dictionary[key]['tests'])
            try:
                if test_position is not None and test['tier'] > dictionary[key]['tests'][test_position]['tier']:
                    # replacing tier with higher one
                    dictionary[key]['tests'][test_position] = test
            except KeyError:
                pass
            if not _is_test_in_tests(test['test'], dictionary[key]['tests']):
                # test is not in yet
                dictionary[key]['tests'].append(test)
    return dictionary


def fmf_filter(filter, node):
    return fmf.utils.filter(filter=filter, data=node)


def get_config(main_dictionary, dictionary=None, conf=list()):
    if dictionary is None:
        dictionary = main_dictionary
        for install in main_dictionary['install']:
            conf.append(remove_redundant(install))
    shuffle(dictionary['tests'])
    for test in dictionary['tests']:
        conf.append(remove_redundant(test))
    for key in dictionary:
        if key not in ['tests', 'install', 'setups']:
            setup = get_setup(main_dictionary, key)
            cleanup = None
            if 'requires_cleanup' in setup:
                cleanup = setup.pop('requires_cleanup')
            conf.append(remove_redundant(setup))
            if isinstance(dictionary[key], dict):
                get_config(main_dictionary, dictionary[key], conf)
            if cleanup is not None:
                cleanup = get_setup(main_dictionary, cleanup)
                conf.append(remove_redundant(cleanup))
                conf, dictionary = insert_install(conf, cleanup)
    return conf


def get_setup(dictionary, name):
    for setup in dictionary["setups"]:
        if setup['name'] == name:
            return setup
    print "FAIL: Could not find setup %s!" % name
    exit(1)
