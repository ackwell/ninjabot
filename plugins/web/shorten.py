
"""
Provides an API to shorten URLs
Currently uses is.gd
"""

import requests


def shorten(url):
	api = 'http://is.gd/create.php'	
	params = {
		'format': 'simple',
		'url': url
	}

	response = requests.get(api, params=params)
	return response.text


APIS = {
	'web.shorten': shorten
}