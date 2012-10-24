class Plugin:
	def __init__(self, bot, config):
		self.bot = bot

	def trigger_test(self, msg):
		if msg.argument:
			self.bot.privmsg(msg.channel, msg.argument)
		else:
			self.bot.privmsg(msg.channel, "This is a test message.")