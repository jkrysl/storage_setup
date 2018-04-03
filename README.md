# storage_setup
This is an example for Flexible Metadata File project found at https://github.com/psss/fmf.

The main purpose of this example is to demonstrate FMF usage for test run creation including setup before tests and cleanup after them based on information provided in metadata.

In 'setup/setup_vdo.py' is an example how to pass FMF metadata to test itself using environment variables.

To run this example, clone it and run these commands, each is for different 'variant' of backing storage:
./run_tests.py --setup "remote"
./run_tests.py --setup "local"

It prints out commands it would run on normal occasion. There are 3 tests:
tests/create/ack_threads.py
tests/create/activate.py
tests/modify/block_map_cache_size.py
The last one requires extra setup on top of the common one (local/remote). Also each setup has its own cleanup.
