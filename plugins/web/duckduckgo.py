"""
Uses DuckDuckGo's instant answer API to find search results.
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
			'no_redirect': '1',
			'skip_disambig': '1'
		}
		request_json = requests.get(url, params=params).json()

		content = ''
		url = ''

		type_ = request_json['Type']
		if type_ == 'A':
			content = "[{}] {}".format(request_json['AbstractSource'], request_json['AbstractText'])

			# If there is a result with the response, use it's URL instead.
			results  = request_json['Results']
			if len(results):
				result = results[0]
				url = "{} ({})".format(self.shorten(result['FirstURL']), result['Text'])
			else:
				url = self.shorten(request_json['AbstractURL'])

		elif type_ == 'C':
			...

		elif type_ == 'N':
			...

		elif type_ == 'E':
			# It might be a !bang redirect, or a calculation or similar.
			if request_json['Redirect']:
				source = 'Redirect'
				answer = self.shorten(request_json['Redirect'])
			else:
				source = request_json['AnswerType']
				answer = request_json['Answer']
			content = "[{}] {}".format(source, answer)

		if url:
			url = " \002::\002 " + url

		message = u"\002DuckDuck\0033Go\003 ::\002 {}{}".format(content, url)
		self.bot.privmsg(msg.channel, message)

	def trigger_duckduckgo(self, msg):
		"Usage: duckduckgo <searchterm>. Shows the instant answer for DuckDuckGo query."
		self.trigger_ddg(msg)