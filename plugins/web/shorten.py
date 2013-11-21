
"""
Provides an API to shorten URLs
Currently uses is.gd
"""

import requests


class Shorten(object):
	def __init__(self):
		self.cache = {}

	def shorten(self, url):
		if url in self.cache:
			return self.cache[url]

		api = 'http://is.gd/create.php'	
		params = {
			'format': 'simple',
			'url': url
		}

		short_url = requests.get(api, params=params).text
		self.cache[url] = short_url
		return short_url


APIS = {
	'web.shorten': Shorten().shorten
}
