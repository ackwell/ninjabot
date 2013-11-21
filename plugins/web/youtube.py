"""
Plugin to search youtube and return the first result, along with some info.
"""

import requests


class Plugin(object):
	def load(self, bot, config):
		self.bot = bot

		self.utils = self.bot.request_api('web.utils')

	def trigger_yt(self, msg):
		"Usage: yt <searchterm>. Prints title and link to first youtube result."
		if len(msg.args) == 0:
			self.bot.notice(msg.nick, "Please specify a search term")
			return

		url = 'https://gdata.youtube.com/feeds/api/videos'
		params = {
			'q':           ' '.join(msg.args),
			'max-results': '1',
			'v':           '2',
			'alt':         'json'
		}
		request_json = requests.get(url, params=params).json()

		if 'entry' not in request_json['feed']:
			self.bot.privmsg(msg.channel, "{}: No entries were found.".format(' '.join(msg.args)))
			return

		entry = request_json['feed']['entry'][0]
		title = self.utils.cull_html(entry['title']['$t'])
		desc  = self.utils.cull_html(entry['media$group']['media$description']['$t'])

		message = u"\002You\0030,4Tube\003 ::\002 {} \002::\002 {} \002::\002 {}".format(title, desc, "http://youtu.be/"+entry['id']['$t'].split(':')[-1],)
		self.bot.privmsg(msg.channel, message)

	def trigger_youtube(self, msg):
		"Usage: youtube <searchterm>. Prints title and link to first youtube result."
		self.trigger_yt(msg)
