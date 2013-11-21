"""
This file makes sure the source code is in the path,
and the NinjabotTestCase makes sure no logging takes place
during testing
"""

import os
import sys
import unittest

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, ROOT)


class NinjabotTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        import ninjabot
        ninjabot.logger.handlers = []
        return super().__init__(*args, **kwargs)

    def assertEndsWith(self, val, end_val):
        return self.assertMultiLineEqual(
            end_val,
            val[-len(end_val):]
        )
