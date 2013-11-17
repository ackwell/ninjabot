# Persistent storage API

import os
import pickle


class Storage(object):
	def __init__(self, plugin, bot):
		try:
			# Set the filename based on the plugin name
			self._fname = '.'.join(plugin.__module__.split('.')[1:])
			self._base_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..')
			self._config = bot.config
			if self._config.get('storage', {}).get('path', False):
				self._path = self._config['storage']['path']
			else:
				self._path = 'storage'

			self._full_path = os.path.normpath(os.path.join(self._base_path, self._path, self._fname))

			if not os.path.exists(os.path.dirname(self._full_path)):
				os.makedirs(os.path.dirname(self._full_path))

			if os.path.exists(self._full_path):
				self._store = pickle.load(open(self._full_path, 'rb'))
			else:
				self._store = {}

			if not self._config.get('storage', {}).get('alwayswrite', False):
				bot.register_storage(self)
		except Exception as e:
			print('EXCEPTION!')
			print(type(e), e.args, e.message)

	def put(self, key, value):
		self._store[key] = value
		if self._config.get('storage', {}).get('alwayswrite', False):
			self.write()

	def get(self, key, default=None):
		return self._store.get(key, default)

	def get_dict(self):
		return self._store

	def __setitem__(self, key, value):
		self.put(key, value)

	def __getitem__(self, key):
		return self.get(key)

	def __contains__(self, key):
		return key in self._store

	def write(self):
		pickle.dump(self._store, open(self._full_path, 'wb'))
