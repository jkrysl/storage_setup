#!/usr/bin/python
# -*- coding: utf-8 -*-

# This is an example how to pass metadata to test using environment variables

from os import environ


def create_vdo():
    print("INFO: Creating vdo.")

    # These are all possible CLI options
    options = ['ack_threads', 'activate', 'bio_rotation_interval', 'bio_threads', 'block_map_cache_size',
               'block_map_period', 'compression', 'conf_file', 'cpu_threads', 'deduplication', 'emulate512', 'force',
               'hash_zone_threads', 'index_mem', 'log_file', 'log_level', 'logical_size', 'multiple_threads',
               'physical_threads', 'read_cache', 'read_cache_size', 'slab_size', 'sprase_index', 'verbose',
               'write_policy']
    arguments = {}
    for opt in options:
        opt = "fmf_" + opt
        if opt in environ:
            arguments[opt] = environ[opt]

    device = environ['fmf_device']
    name = environ ['fmf_device']

    params = ""
    for arg in arguments:
        value = arguments[arg]
        param = arg.split("_")
        params += "--" + param.pop(0) + "".join([x.upper() for x in param]) + "=%s " % value

    print "Running 'vdo create --name %s --device %s %s" % (name, device, params)
    return


if __name__ == "__main__":
    create_vdo()
