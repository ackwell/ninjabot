# git plugin
# allows 'git pull' to be run remotely

import time

class Plugin(object):
	def __init__(self, bot, config):
		self.bot = bot
		self.git = self.bot.request_api('git').Git()

	def trigger_gitpull(self, msg):
		if self.bot.is_admin(msg.nick):
			self.bot.notice(msg.nick, 'Running git pull...')
			response = self.git.pull()
			for line in response.split('\n'):
				self.bot.notice(msg.nick, line)
				time.sleep(0.2)
			self.bot.notice(msg.nick, 'Done!')
