import os
import sys
import unittest

TEST_DIR = os.path.dirname(__file__)

sys.path.insert(0, os.path.join(TEST_DIR, '..'))


def main():
    loader = unittest.TestLoader()
    suite = loader.discover(TEST_DIR)

    runner = unittest.TextTestRunner(verbosity=2)
    # wait a second or so for things to start

    end = runner.run(suite)
    if len(end.errors) > 0 or len(end.failures) > 0:
        sys.exit('{} errors appear to have occured.'.format(len(end.errors)))


if __name__ == '__main__':
    main()
