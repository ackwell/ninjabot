# Persistent storage API

import os
import pickle
import warnings


class Storage(dict):
	def __init__(self, plugin, bot):
		# Set the filename based on the plugin name
		self._fname = '.'.join(plugin.__module__.split('.')[1:])
		self._base_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
		self._config = bot.config

		if self._config.get('storage', {}).get('path', False):
			self._path = self._config['storage']['path']
		else:
			self._path = 'storage'

		self._path = os.path.join(self._base_path, self._path)
		self._full_path = os.path.normpath(os.path.join(self._path, self._fname))

		if not os.path.exists(self._path):
			os.makedirs(self._path)

		if os.path.exists(self._full_path):
			with open(self._full_path, 'rb') as fh:
				self.update(pickle.load(fh))

		if not self._config.get('storage', {}).get('alwayswrite', False):
			bot.register_storage(self)

	def __repr__(self):
		return '<Store location="{}">'.format(self._full_path)

	def put(self, key, value):
		warnings.warn('This method is deprecated; just use the storage object directly')
		self[key] = value

	def __setitem__(self, *args, **kwargs):
		super().__setitem__(*args, **kwargs)
		if self._config.get('storage', {}).get('alwayswrite', False):
			self.write()

	def get_dict(self):
		warnings.warn('This method is deprecated; just use the storage object directly')
		return self

	def write(self):
		with open(self._full_path, 'wb') as fh:
			pickle.dump(self, fh)


APIS = {
	'core.storage': Storage
}
