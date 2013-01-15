

class Plugin:
	def __init__(self, bot, config):
		self.bot = bot

	def trigger_mafia(self, msg):
		"Mafia: THAT'S MAFIA TALK! For a list of commands, run `mafia help`"
		if len(msg.args) == 0:
			self.bot.notice(msg.nick, "Please specify an Mafia command. Check `%smafia help` for avaliable commands."%self.bot.command_prefix)
			return

		command = msg.args.pop(0).lower()
		if 'mafia_'+command in dir(self):
			getattr(self, 'mafia_'+command)(msg)
		else:
			self.bot.notice(msg.nick, "The command '%s' does not exist. Check `%smafia help` for avalable commands."%(command, self.bot.command_prefix))
	
	def mafia_help(self, msg):
		self.bot.notice(msg.nick, "NOT IMPLEMENTED")

	def mafia_jointest(self, msg):
		self.bot.join('##ninjabot-mafia-town-test')
		self.bot.mode('##ninjabot-mafia-town-test', '+is')
		self.bot.invite('ackwell', '##ninjabot-mafia-town-test')