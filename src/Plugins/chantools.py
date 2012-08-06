class Plugin:
	def __init__(self, controller):
		self.c = controller

	def trigger_join(self, msg):
		"Usage: join <channel>. Makes the bot join <channel>. Admin only."
		if msg and not self.c.is_admin(msg.nick):
			self.c.notice(msg.nick, "You are not permitted to use this command.")
			return

		if len(msg.args) == 0:
			self.c.notice(msg.nick, "No channel was specified.")

		chan = msg.args[0]
		if chan in self.c.channels:
			self.c.notice(msg.nick, "I am already on "+chan)
			return

		self.c.join(chan)
		self.c.channels.append(chan)

	def trigger_part(self, msg):
		"Usage: part <channel>. Makes the bot leave <channel>. Admin only."
		if msg and not self.c.is_admin(msg.nick):
			self.c.notice(msg.nick, "You are not permitted to use this command.")
			return

		if len(msg.args) == 0:
			self.c.notice(msg.nick, "No channel was specified.")

		chan = msg.args[0]
		if chan not in self.c.channels:
			self.c.notice(msg.nick, "I am not on "+chan)
			return

		self.c.part(chan)
		self.c.channels.remove(chan)