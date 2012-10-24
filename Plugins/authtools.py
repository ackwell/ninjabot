# Removed OP/Voice stuff for now
class Plugin:
	def __init__(self, bot, admins):
		self.bot = bot
		self.admins = admins

	def on_incoming(self, msg):
		if msg.command == 'NOTICE' and msg.nick == "NickServ" and '->' in msg.body:
			args = msg.body.split()
			if args[2] in self.admins and args[4] == '3':
				self.bot.admins.append(args[0])
				self.bot.notice(args[0], "You have been added as an admin.")
			else:
				self.bot.notice(args[0], "You are not an admin.")

		elif msg.command == 'NICK':
			if msg.nick in self.bot.admins:
				self.bot.admins.remove(msg.nick)
				self.bot.notice(msg.body, "Nickname change detected. Please reauth.")
			elif msg.body in self.bot.admins:
				self.bot.admins.remove(msg.body)
				self.bot.notice(msg.body, "Nickname change detected. Please reauth.")

		elif msg.command == 'JOIN':
			if msg.nick in self.bot.admins:
				self.bot.admins.remove(msg.nick)
				self.bot.notice(msg.nick, "This nick has been deauthed. Please reauth.")

	def trigger_auth(self, msg):
		"Checks with NickServ, then adds you to admins list."
		if msg.nick in self.bot.admins:
			self.bot.notice(msg.nick, "You are already an admin.")
			return
		self.bot.privmsg("NickServ", "ACC %s *"%msg.nick)

	def trigger_deauth(self, msg):
		"Deauths an admin, for security purposes."
		if msg.nick not in self.bot.admins:
			self.bot.notice(msg.nick, 'You are not an admin')
			return
		self.bot.admins.remove(msg.nick)
		self.bot.notive(msg.nick, "You have been sucessfully deauthed.")
