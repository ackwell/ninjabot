"""
Provides Wikipedia search functionality
"""

import re
import requests
from bs4 import BeautifulStoneSoup


class Plugin(object):
	def load(self, bot, config):
		self.bot = bot

		self.shorten = self.bot.request_api('web.shorten')

		self.language = 'en'
		if 'language' in config:
			self.language = config['language']

	def trigger_w(self, msg):
		"Usage: w <search term>. Prints a short description of the corresponding wikipedia article."
		if len(msg.args) == 0:
			self.bot.notice(msg.nick, "Please specify a search term")
			return

		params = {
			'action': 'opensearch',
			'format': 'xml',
			'limit': '2',
			'search': ' '.join(msg.args)
		}
		url = 'http://{:s}.wikipedia.org/w/api.php'.format(self.language)

		response = BeautifulStoneSoup(requests.post(url, data=params).text)

		# Damn BS4 is case sensitive, hence all the regex.
		if response.find(re.compile('text', re.I)):
			index = 0
			if "may refer to:" in response.find(re.compile('description', re.I)).string:
				index = 1

			info = response.find_all(re.compile('description', re.I))[index].string.strip()
			url = response.find_all(re.compile('url', re.I))[index].string

			short_url = self.shorten(url)

			message = u"\002Wikipedia ::\002 {} \002::\002 {}".format(info, short_url)
			self.bot.privmsg(msg.channel, message)
		else:
			self.bot.privmsg(msg.channel, "{}: no articles were found.".format(' '.join(msg.args)))

	def trigger_wiki(self, msg):
		"Usage: wiki <search term>. Prints a short description of the corresponding wikipedia article."
		self.trigger_w(msg)
