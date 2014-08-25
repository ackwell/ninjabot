
class Plugin:
	def load(self, bot, config):
		self.bot = bot
		self.config = config
		self.store = self.bot.request_api('core.storage')(self, bot)

	def on_incoming(self, msg):
		text = msg.body.split()
		
		for word in text:
			if word.endswith('++'):
				word = word.rstrip('+')
				amount = 1
			elif word.endswith('--'):
				word = word.rstrip('-')
				amount = -1
			else:
				continue

			if not word:
				continue

			# Use brackets to do things like (C++)++
			if word[0] == '(' and word[-1] == ')':
				word = word[1:-1]

			if not word:
				continue

			self.store[word] = self.store.get(word, 0) + amount

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

	def trigger_mergerep(self, msg):
		if not self.bot.is_admin(msg.nick):
			return

		words = set(msg.args)

		if len(words) < 2:
			self.bot.notice(msg.nick, 'You must choose at least 2 different words to merge')
			return

		notin = ', '.join(w for w in words if w not in self.store)
		if notin:
			self.bot.notice(msg.nick, 'I do not know the words {}'.format(notin))
			return

		key = msg.args[0]
		self.store[key] = sum(self.store[w] for w in words)
		for word in words - {key}:
			del self.store[word]

		successmsg = 'Successfully merged. {} now has a rep of {}'.format(key, self.store[key])
		self.bot.notice(msg.nick, successmsg)

	def trigger_setrep(self, msg):
		if not self.bot.is_admin(msg.nick):
			return

		if len(msg.args) != 2:
			self.bot.notice(msg.nick, 'Usage: setrep <word> <rep>')
			return

		try:
			rep = int(msg.args[1])
		except ValueError:
			self.bot.notice(msg.nick, 'Rep must be an integer')
			return

		word = msg.args[0]
		self.store[word] = rep

		self.bot.notice(msg.nick, 'Successfully set rep of {} to {}'.format(word, rep))


