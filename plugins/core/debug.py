
class Plugin(object):
	def __init__(self, bot, config):
		self.bot = bot
		self.cache = {}
		self.paste = self.bot.request_api('paste')

	def trigger_error(self, msg):
		"Pastebins the latest latest error message. If an index is specified, will return that error instead."
		if not self.bot.is_admin(msg.nick):
			return

		if len(msg.args) == 0:
			err = -1
		else:
			try:
				err = int(msg.args[0])
			except:
				self.bot.notice(msg.nick, 'Please specify a valid error index.')
				return

		try:
			if err in self.cache:
				m = self.cache[err]
			else:
				m = self.paste.write(self.bot.errors[err])
				if err > 0 and 'err' not in m:
					self.cache[err] = m
			self.bot.notice(msg.nick, 'Error report: ' + m)
		except IndexError:
			self.bot.notice(msg.nick, 'No error with that index exists')
