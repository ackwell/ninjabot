class Plugin:
	def __init__(self, controller, bot):
		self.c = controller
		self.timeouts = {}

	def on_incoming(self, msg):
		if msg.command == 'NICK':
			if msg.nick in self.c.ignored:
				self.c.ignored.remove(msg.nick)
				self.c.ignored.append(msg.body)
				if msg.body in self.timeouts: self.timeouts[msg.body] = self.timeouts[msg.nick]
				del self.timeouts[msg.nick]

	def trigger_ignore(self, msg):
		"Usage: `ignore <user> [time]`. Ignores the specified person for [time] (minutes). If [time] is not specified, will remain ignored untill removed."
		if not self.c.is_admin(msg.nick):return

		if len(msg.args) == 0: self.c.notice(msg.nick, "No nick was specified.")
		i = msg.args.pop(0)
		if i in self.c.ignored: self.c.notice(msg.nick, "%s is already ignored"%i)
		self.c.ignored.append(i)
		time = 0
		if len(msg.args) > 0:
			try: time = int(msg.args.pop(0))
			except ValueError:
				self.c.notice(msg.nick, "An invalid time was specified.")
				return
			self.timeouts[i] = time
		self.c.notice(msg.nick, "Ignored %s%s."%(i, ' for %s minutes'%time if time else ''))
		self.c.notice(i, "You have been ignored%s."%(' for %s minutes'%time if time else ''))

	def trigger_allow(self, msg):
		"Usage: `allow <user>`. Removes <user> from the ignore list."
		if not self.c.is_admin(msg.nick):return

		if len(msg.args) == 0: self.c.notice(msg.nick, "No nick was specified.")
		i = msg.args.pop(0)
		if not i in self.c.ignored:self.c.notice(msg.nick, "%s is not on the ignore list."%i)
		self.c.ignored.remove(i)
		if i in self.timeouts: del self.timeouts[i]
		self.c.notice(msg.nick, "%s is no longer ignored."%i)
		self.c.notice(i, "You are no longer ignored.")

	def timer_60(self):
		for k, v in self.timeouts.items():
			if v > 0:
				self.timeouts[k] -= 1
				continue
			self.c.ignored.remove(k)
			del self.timeouts[k]
			self.c.notice(k, "You are no longer ignored.")
