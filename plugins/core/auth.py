# Removed OP/Voice stuff for now
class Plugin(object):
	def load(self, bot, config):
		self.bot = bot
		self.admins = config['admins']
		if not 'ns_'+config['mode'] in dir(self):
			raise ValueError('core.auth->mode is set to an unsupported value')
		self.mode = config['mode'].lower()

		# Clear out the bot's admins on load. Prevents carry-over on plugin reload
		self.bot.admins = []

	def on_incoming(self, msg):
		getattr(self, 'ns_'+self.mode)(msg)

		if msg.command == 'NICK':
			if msg.nick in self.bot.admins:
				self.bot.admins.remove(msg.nick)
				self.bot.notice(msg.body, 'Nickname change detected. Please reauth.')
			elif msg.body in self.bot.admins:
				self.bot.admins.remove(msg.body)
				self.bot.notice(msg.body, 'Nickname change detected. Please reauth.')

		elif msg.command == 'JOIN':
			if msg.nick in self.bot.admins:
				self.bot.admins.remove(msg.nick)
				self.bot.notice(msg.nick, 'This nick has been deauthed. Please reauth.')

	def ns_status(self, msg):
		if msg.command == 'NOTICE' and msg.nick == 'NickServ' and 'STATUS' in msg.body:
			args = msg.body.split()
			if args[1] in self.admins and args[2] == '3':
				self.bot.admins.append(args[1])
				self.bot.notice(args[1], 'You have been added as an admin.')
			else:
				self.bot.notice(args[1], 'You are not an admin.')

	def ns_acc(self, msg):
		if msg.command == 'NOTICE' and msg.nick == 'NickServ' and '->' in msg.body:
			args = msg.body.split()
			if args[2] in self.admins and args[4] == '3':
				self.bot.admins.append(args[0])
				self.bot.notice(args[0], 'You have been added as an admin.')
			else:
				self.bot.notice(args[0], 'You are not an admin.')

	def trigger_auth(self, msg):
		'Checks with NickServ, then adds you to admins list.'
		if msg.nick in self.bot.admins:
			self.bot.notice(msg.nick, 'You are already an admin.')
			return
		if self.mode == 'acc':
			self.bot.privmsg('NickServ', 'ACC {0} *'.format(msg.nick))
		elif self.mode == 'status':
			self.bot.privmsg('NickServ', 'STATUS {0}'.format(msg.nick))

	def trigger_deauth(self, msg):
		'Deauths an admin, for security purposes.'
		if msg.nick not in self.bot.admins:
			self.bot.notice(msg.nick, 'You are not an admin')
			return
		self.bot.admins.remove(msg.nick)
		self.bot.notice(msg.nick, 'You have been successfully deauthed.')
