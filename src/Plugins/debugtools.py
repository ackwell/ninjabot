from apis import kdepaste

class Plugin:
	def __init__(self, controller):
		self.c = controller

		self.cache = {}

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
			if err in self.cache:
				m = self.cache[err]
			else:
				m = kdepaste.write(self.c.errors[err])
				if err > 0 and 'err' not in m:
					self.cache[err] = m
			self.c.notice(msg.nick, "Error report: %s"%m)
			return
		except IndexError: self.c.notice(msg.nick, "No error with that index exists")