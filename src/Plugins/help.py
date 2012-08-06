class Plugin:
	def __init__(self, controller):
		self.c = controller

	def trigger_help(self, msg):
		"Usage: help [trigger]. Lists avaliable triggers. If trigger is specified, will print help for that trigger (if avaliable)."

		prefix = self.c.plugins.prefix
		if len(msg.args) == 0:
			self.c.notice(msg.nick, 'Avaliable triggers:')
			self.c.notice(msg.nick, prefix+(', '+prefix).join(self.c.plugins.triggers.keys()))
			self.c.notice(msg.nick, 'For further info, type '+prefix+'help <trigger>')
		else:
			doc = self.c.plugins.triggers[msg.args[0].lstrip(prefix)].__doc__
			if doc:
				self.c.notice(msg.nick, doc)
			else:
				self.c.notice(msg.nick, "Either that trigger does not exist, or it has no documentation.")