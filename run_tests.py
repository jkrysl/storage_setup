#!/usr/bin/python

import argparse
from tools.fmf_tools import get_tests, get_config, get_path


def _execute_tests_fmf(path, filter=list(""), setup_env=None):

    tests = get_tests(path, filter, os_env_asterix=setup_env)
    config = get_config(tests)

    for test in config:
        # skip comments
        if not isinstance(test, dict):
            continue

        if 'test' not in test:
            print("FAIL: Could not find test file for %s. Check its metadata for correct path." % test['name'])
            return False

        command = ""
        # Add metadata as environment variables
        for att in test:
            if att == 'test':
                continue
            command += "fmf_%s='%s' " % (att, test[att])

        command += get_path() + "/" + test['test']

        print("Running command:")
        print("\t%s" % command)
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='run-test')
    parser.add_argument('--filter', '-f', required=False, dest="filter", type=str,
                            default=list(""), help="String of filters.", action="append")
    parser.add_argument('--path', required=False, dest="path",
                            default="", help="Relative path from tests/")
    parser.add_argument('--setup', required=False, dest="setup",
                            default=None, help="Setup string to replace '*' in required_setup.")

    args = parser.parse_args()

    # args.setup = "iscsi vdo/setup/cleanup_multipath"
    test_runs = _execute_tests_fmf(args.path, args.filter, args.setup)
