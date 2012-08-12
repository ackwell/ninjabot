from apis import pastebin

class Plugin:
	def __init__(self, controller):
		self.c = controller

	def trigger_error(self, msg):
		"Pastebins the latest latest error message. If an index is specified, will return that error instead."
		if not self.c.is_admin(msg.nick): return

		if len(msg.args) == 0:
			err = -1
		else:
			try: err = int(msg.args[0])
			except:
				self.c.notice(msg.nick, "Please specify a valid error index.")
				return
		try:
			e = self.c.errors[err]
			self.c.notice(msg.nick, "Error report: %s"%pastebin.write(e, self.c.config))
			return
		except IndexError: self.c.notice(msg.nick, "No error with that index exists")