class Plugin(object):
	def load(self, bot, config):
		self.bot = bot

	def trigger_join(self, msg):
		"Joins the specified channels. Usage: `join <#foo,#bar fubar>`. Joins #foo using key `fubar` and joins #bar without a key. Syntax is the same as RFC 2812, sans usage of `JOIN 0`"
		if not self.bot.is_admin(msg.nick):
			return

		if len(msg.args) == 0:
			self.bot.notice(msg.nick, "No channels were specified.")
		channels = msg.args.pop(0)
		if len(msg.args) > 0:
			keys = msg.args.pop(0)
		else: keys = ""
		self.bot.irc_send('JOIN {0} {1}'.format(channels, keys))

	def trigger_part(self, msg):
		"Leaves the specified channels. Usage: `part <#foo,#bar (fubar)>`. Parts #foo and #bar. If present, part message `fubar` is sent."
		if not self.bot.is_admin(msg.nick):
			return

		if len(msg.args) == 0:
			self.bot.notice(msg.nick, "No channels were specified.")
		channels = msg.args.pop(0)
		if len(msg.args) > 0:
			partmsg = msg.args.pop(0)
		else: partmsg = ""
		self.bot.irc_send('PART {0} {1}'.format(channels, partmsg))