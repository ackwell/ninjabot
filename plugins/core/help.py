class Plugin(object):
	def __init__(self, bot, config):
		self.bot = bot

	def trigger_help(self, msg):
		"Usage: help [trigger]. Lists avaliable triggers. If trigger is specified, will print help for that trigger (if avaliable)."

		prefix = self.bot.command_prefix
		if len(msg.args) == 0:
			self.bot.notice(msg.nick, 'Avaliable triggers:')
			self.bot.notice(msg.nick, prefix+(', '+prefix).join(sorted(self.bot.triggers.keys())))
			self.bot.notice(msg.nick, 'For further info, type {0}help <trigger>'.format(prefix))
		else:
			if msg.args[0].lstrip(prefix) in self.bot.triggers:
				doc = self.bot.triggers[msg.args[0].lstrip(prefix)].__doc__
				if doc:
					self.bot.notice(msg.nick, doc)
				else:
					self.non_existent_help(msg)
			else:
				self.non_existent_help(msg)

	def non_existent_help(self, msg):
		self.bot.notice(msg.nick, "Either that trigger does not exist, or it has no documentation.")
