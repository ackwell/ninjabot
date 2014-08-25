import requests

class Paste(object):
	def write(self, string, private=True, expire=3600):
		"""
		Write <string> to a new kdepaste
		Returns kdepaste URL or error message
		"""

		# There are only certain values that are valid expiry times
		# This ensures the paste will stay for at least the specified time
		# Uncomment the following two lines to get dynamic expire values
		#expres = requests.get('http://paste.kde.org/api/json/parameter/expire')
		#valid_expire = json.loads(expres.text)['result']['values']
		valid_expire = [1800, 21600, 86400, 604800, 2592000, 31536000]
		orig_expire = expire
		expire = max(valid_expire)
		for length in valid_expire:
			if length >= orig_expire and length < expire:
				expire = length

		url = 'http://paste.kde.org/api/json/create'
		data = {
			'data': string,
			'language': 'text',
			'expire': expire
		}
		if private:
			data['private'] = 'true'

		res = requests.post(url, data=data)
		j = res.json()['result']

		if 'error' in j:
			return j['error']

		o = ''
		if private:
			o = 'http://paste.kde.org/{:s}/{:s}'.format(j['id'], j['hash'])
		else:
			o = 'http://paste.kde.org/{:s}'.format(j['id'])

		return o


APIS = {
	# Making an instance to preserve old API
	'core.paste': Paste()
}
