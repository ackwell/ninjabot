import unittest
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


@patch('ninjabot.Bot')
class TestStorageAPI(unittest.TestCase):
    def setUp(self):
        bot = MagicMock(name='bot')
        plugin = MagicMock(name='plugin', __module__='data.db')

        from apis import storage
        self.store = storage.Storage(plugin, bot)

    def test_init(self, bot):
        pass

    @patch('pickle.dumps')
    def test_write(self, bot, dumps):
        import pudb
        pu.db
        self.store.write()

def main():
    unittest.main()

if __name__ == '__main__':
    main()
