class Plugin(object):
	def __init__(self, bot, config):
		self.bot = bot
		self.timeouts = {}

	def on_incoming(self, msg):
		if msg.command == 'NICK':
			if msg.nick in self.bot.ignored:
				self.bot.ignored.remove(msg.nick)
				self.bot.ignored.append(msg.body)
				if msg.body in self.timeouts:
					self.timeouts[msg.body] = self.timeouts[msg.nick]
				del self.timeouts[msg.nick]

	def trigger_ignore(self, msg):
		"Usage: `ignore <user> [time]`. Ignores the specified person for [time] (minutes). If [time] is not specified, will remain ignored untill removed."
		if not self.bot.is_admin(msg.nick):
			return

		if len(msg.args) == 0:
			self.bot.notice(msg.nick, "No nick was specified.")
		i = msg.args.pop(0)
		if i in self.bot.ignored:
			self.bot.notice(msg.nick, "{0} is already ignored".format(i))
		self.bot.ignored.append(i)
		time = 0
		if len(msg.args) > 0:
			try:
				time = int(msg.args.pop(0))
			except ValueError:
				self.bot.notice(msg.nick, "An invalid time was specified.")
				return
			self.timeouts[i] = time

		if time:
			self.bot.notice(msg.nick, "Ignored {0}{1}.".format(i, ' for {0} minutes'.format(time)))
			self.bot.notice(i, "You have been ignored{0}.".format(' for {0} minutes'.format(time)))

	def trigger_allow(self, msg):
		"Usage: `allow <user>`. Removes <user> from the ignore list."
		if not self.bot.is_admin(msg.nick):
			return

		if len(msg.args) == 0:
			self.bot.notice(msg.nick, "No nick was specified.")

		person = msg.args.pop(0)
		if not person in self.bot.ignored:
			self.bot.notice(msg.nick, "{:s} is not on the ignore list.".format(person))

		self.bot.ignored.remove(person)

		if person in self.timeouts:
			del self.timeouts[person]

		self.bot.notice(msg.nick, "{:s} is no longer ignored.".format(person))
		self.bot.notice(person, "You are no longer ignored.")

	def timer_60(self):
		to_del = []
		for k, v in self.timeouts.items():
			if v > 0:
				self.timeouts[k] -= 1
				continue
			to_del.append(k)

		for user in to_del:
			self.bot.ignored.remove(user)
			del self.timeouts[user]
			self.bot.notice(user, "You are no longer ignored.")
