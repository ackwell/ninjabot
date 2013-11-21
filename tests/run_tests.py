import os
import sys
import unittest

TEST_DIR = os.path.dirname(__file__)

sys.path.insert(0, os.path.join(TEST_DIR, '..'))


def main():
    loader = unittest.TestLoader()
    suite = loader.discover(TEST_DIR)

    runner = unittest.TextTestRunner(verbosity=2)

    end = runner.run(suite)
    if len(end.errors) > 0 or len(end.failures) > 0:
        sys.exit('{} failures appear to have occured.'.format(
            len(end.errors) + len(end.failures)
        ))


if __name__ == '__main__':
    main()
