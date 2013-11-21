from common import NinjabotTestCase

import os
import unittest
from unittest.mock import patch, MagicMock


# we patch makedirs to make sure no directories are ever created
@patch('os.makedirs')
class TestStorage(NinjabotTestCase):
	def test_init_default_config(self, makedirs):
		import ninjabot

		bot = MagicMock(name='bot', config={}, spec=ninjabot.Ninjabot)
		plugin = MagicMock(name='plugin', __module__='plugins.misc.test')

		from plugins.core import storage
		store = storage.Storage(plugin, bot)

		self.assertEqual(store._fname, 'misc.test')
		self.assertEndsWith(store._base_path, 'ninjabot')
		self.assertEqual(store._config, {})
		self.assertEndsWith(store._path, os.path.join('ninjabot', 'storage'))
		self.assertEndsWith(store._full_path, os.path.join('ninjabot', 'storage', 'misc.test'))

		bot.register_storage.assert_called_with(store)

	def test_init_custom_config(self, makedirs):
		import tempfile
		config = {'storage': {
			'path': tempfile.mkdtemp(),
			'alwayswrite': True
		}}

		import ninjabot
		bot = MagicMock(name='bot', config=config, spec=ninjabot.Ninjabot)
		plugin = MagicMock(name='plugin', __module__='plugins.misc.test')

		from plugins.core import storage
		store = storage.Storage(plugin, bot)
		store
		# TODO; fill in rest

	@patch('plugins.core.storage.Storage.write')
	def test_alwayswrite(self, write, makedirs):
		import ninjabot
		config = {'storage': {'alwayswrite': True}}

		bot = MagicMock(name='bot', config=config, spec=ninjabot.Ninjabot)
		plugin = MagicMock(name='plugin', __module__='plugins.misc.test')

		from plugins.core import storage
		store = storage.Storage(plugin, bot)
		store['hello'] = 'world'

		write.assert_called_with()

	def test_write(self, mkdirs):
		import ninjabot

		bot = MagicMock(name='bot', config={}, spec=ninjabot.Ninjabot)
		plugin = MagicMock(name='plugin', __module__='plugins.misc.test')

		from plugins.core import storage
		store = storage.Storage(plugin, bot)

		import tempfile
		fd, store._full_path = tempfile.mkstemp()

		store.data = {'world': 'is wonderful'}
		store.write()

		with open(store._full_path, 'rb') as fh:
			data = fh.read()

		self.assertEqual(
			data,
			b'\x80\x03}q\x00X\x05\x00\x00\x00worldq'
			b'\x01X\x0c\x00\x00\x00is wonderfulq\x02s.'
		)


def main():
	unittest.main()

if __name__ == '__main__':
	main()
