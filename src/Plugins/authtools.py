
class Plugin:
	def __init__(self, controller):
		self.c = controller

		self.op_chars = '@'
		self.voice_chars = '+'

	def on_incoming(self, msg):
		if msg.command == '353':
			nicks = msg.body.split()
			for nick in nicks:
				if nick[0] in self.op_chars:
					self.c.ops.append(nick[1:])
				elif nick[0] in self.voice_chars:
					self.c.voiced.append(nick[1:])

		elif msg.command == msg.MODE:
			if msg.body[1] in 'vo':
				mode, nick = msg.body.split()
				l = self.c.ops if mode[1] == 'o' else self.c.voiced
				if mode[0] == '-':
					l.remove(nick)
				elif mode[0] == '+':
					l.append(nick)

		elif msg.command == msg.NOTICE and msg.nick == "NickServ":
			args = msg.body.split()
			if args[2] in self.c.sl.config['config']['admins'] and args[4] == '3':
				self.c.admins.append(args[0])
				self.c.notice(args[0], "You have been added as an admin.")
			else:
				self.c.notice(args[0], "You are not an admin.")

		elif msg.command == msg.NICK:
			if msg.nick in self.c.admins:
				self.c.admins.remove(msg.nick)
				self.c.notice(msg.body, "Nickname change detected. Please reauth.")
			elif msg.body in self.c.admins:
				self.c.admins.remove(msg.body)
				self.c.notice(msg.body, "Nickname change detected. Please reauth.")

		elif msg.command == msg.JOIN:
			if msg.nick in self.c.admins:
				self.c.admins.remove(msg.nick)
				self.c.notice(msg.nick, "This nick has been deauthed. Please reauth.")



	def trigger_auth(self, msg):
		"Checks with NickServ, then adds you to admins list."
		if msg.nick in self.c.admins:
			self.c.notice(msg.nick, "You are already an admin.")
			return
		self.c.privmsg("NickServ", "ACC %s *"%msg.nick)

	def trigger_deauth(self, msg):
		"Deauths an admin, for security purposes."
		if msg.nick not in self.c.admins:
			self.c.notice(msg.nick, 'You are not an admin')
			return
		self.c.admins.remove(msg.nick)
		self.c.notive(msg.nick, "You have been sucessfully deauthed.")
