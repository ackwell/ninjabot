"""
Trigger that prints first google result for the search query provided
"""

import requests


class Plugin(object):
	def load(self, bot, config):
		self.bot = bot

		self.shorten = self.bot.request_api('web.shorten')
		self.utils = self.bot.request_api('web.utils')

	def trigger_g(self, msg):
		"Usage: g <search term>. Prints title & short description of first google result."
		if len(msg.args) == 0:
			self.bot.notice(msg.nick, "Please specify a search term")
			return

		url = 'http://ajax.googleapis.com/ajax/services/search/web'
		params = {
			'q': ' '.join(msg.args),
			'v': 1.0
		}
		response_json = requests.get(url, params=params).json()

		results = response_json['responseData']['results']
		if len(results) == 0:
			self.bot.privmsg(msg.channel, "{}: No results.".format(' '.join(msg.args)))
			return
		top_result = results[0]

		url     = self.shorten(top_result['url'])
		content = self.utils.cull_html(top_result['content'])
		title   = self.utils.cull_html(top_result['title'])

		message = u"\002\0032G\0034o\0038o\0032g\0033l\0034e\003 ::\002 {} \002::\002 {} \002::\002 {}".format(title, content, url)
		self.bot.privmsg(msg.channel, message)

	def trigger_google(self, msg):
		"Usage: google <search term>. Prints title & short description of first google result."
		self.trigger_g(msg)