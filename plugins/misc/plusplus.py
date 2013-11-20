
class Plugin:
	def load(self, bot, config):
		self.bot = bot
		self.config = config
		self.store = self.bot.request_api('core.storage')(self, bot)

	def on_incoming(self, msg):
		text = msg.body.split()
		if not text or len(text) > 2:
			return

		# Space between ++ and word:
		if len(text) == 2:
			word = text[0]
			incr = text[1]
			if not incr.strip('+'):
				amount = len(incr)/2
			elif not incr.strip('-'):
				amount = -len(incr)/2
			else:
				return

		if len(text) == 1:
			word = text[0]
			if word.endswith('++'):
				amount = (len(word) - len(word.rstrip('+')))/2
				word = word.rstrip('++')
			elif word.endswith('--'):
				amount = -(len(word) - len(word.rstrip('-')))/2
				word = word.rstrip('--')
			else:
				return

		if not word:
			return

		if word not in self.store:
			self.store[word] = 0

		self.store[word] += amount

		return

	def trigger_rep(self, msg):
		if msg.args:
			counts = {}
			for word in msg.args:
				counts[word] = self.store.get(word, 0)
		else:
			counts = {}
			for key in self.store:
				if self.store[key]:
					counts[key] = self.store[key]

		if counts:
			ret = []
			length = 0
			for word, count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
				ret.append('{}: {}'.format(word, count))
				length += len(ret[-1]) + 2
				if length > 180:
					ret.append('...')
					break
			ret = ', '.join(ret)
		else:
			ret = 'No rep has been given!'

		self.bot.privmsg(msg.channel, ret)

	def trigger_karma(self, msg):
		self.trigger_rep(msg)
