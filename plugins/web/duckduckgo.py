"""
Uses DuckDuckGo's instand answer API to find search results.
"""

import requests


class Plugin(object):
	def load(self, bot, config):
		self.bot = bot

		self.shorten = self.bot.request_api('web.shorten')

	def trigger_ddg(self, msg):
		"Usage: ddg <searchterm>. Shows the instant answer for DuckDuckGo query."
		if len(msg.args) == 0:
			self.bot.notice(msg.nick, "Please specify a search term")
			return

		url = 'http://api.duckduckgo.com/'
		params = {
			'q': ' '.join(msg.args),
			'format': 'json',
			'no_html': '1',
			'skip_disambig': '1'
		}
		request_json = requests.get(url, params=params).json()

		results  = request_json['Results']
		abstract = request_json['AbstractText']
		source   = request_json['AbstractSource']

		# If there was a result in the response, use the link from it instead
		url = ''
		if len(results):
			result = results[0]
			url = "{} ({})".format(self.shorten(result['FirstURL']), result['Text'])
		else:
			url = self.shorten(request_json['AbstractURL'])

		message = u"\002DuckDuck\0033Go\003 ::\002 [{}] {} \002::\002 {}".format(source, abstract, url)
		self.bot.privmsg(msg.channel, message)

	def trigger_duckduckgo(self, msg):
		"Usage: duckduckgo <searchterm>. Shows the instant answer for DuckDuckGo query."
		self.trigger_ddg(msg)