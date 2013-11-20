# Persistent storage API

import os
import pickle
import warnings
import collections


class Storage(collections.UserDict):
	def __init__(self, plugin, bot):
		# initiate the UserDict
		super().__init__()

		# Set the filename based on the plugin name
		self._fname = plugin.__module__.partition('.')[-1]
		self._base_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
		self._base_path = os.path.abspath(self._base_path)

		self._config = bot.config.get('storage', {})
		self._path = self._config.get('path', 'storage')

		self._path = os.path.join(self._base_path, self._path)
		self._full_path = os.path.normpath(os.path.join(self._path, self._fname))

		if not os.path.exists(self._path):
			os.makedirs(self._path)

		if os.path.exists(self._full_path):
			with open(self._full_path, 'rb') as fh:
				self.data.update(pickle.load(fh))

		if not self._config.get('alwayswrite', False):
			bot.register_storage(self)

	def __repr__(self):
		return '<Storage location="{}">'.format(self._full_path)

	def put(self, key, value):
		warnings.warn('This method is deprecated; just use the storage object directly')
		self[key] = value

	def __setitem__(self, key, value):
		super().__setitem__(key, value)
		if self._config.get('alwayswrite', False):
			self.write()

	def get_dict(self):
		warnings.warn('This method is deprecated; just use the storage object directly')
		return self

	def write(self):
		with open(self._full_path, 'wb') as fh:
			pickle.dump(self.data, fh)


APIS = {
	'core.storage': Storage
}
