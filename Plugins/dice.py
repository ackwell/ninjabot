# Dice plugin
# Written by Cyphar
# Do whatever you want with this.

class Plugin:
	# Modes
	SINGLE = 1
	MULTIPLE = 2
	DEFAULT = MULTIPLE

	# Face size limits
	F_LOWER_LIMIT = 1
	F_UPPER_LIMIT = 20

	# Number of dice limits
	D_LOWER_LIMIT = 1
	D_UPPER_LIMIT = 20

	def __init__(self, bot, config):
		self.bot = bot
		self.config = config

	def trigger_dice(self, msg):
		"""
		Roll a die (or dice).
		dice <sides=6> <times=1>
		"""

		# Too many arguments
		if len(msg.args) > 2:
			self.bot.notice(msg.nick, 'Invalid number of arguments.')
			return

		# Default options
		options = [6, 1]

		# Convert args to options
		for arg in enumerate(msg.args):
			if not arg[1].isnumeric():
				self.bot.notice(msg.nick, 'Invalid argument %r.' % arg[1])
				return

			options[arg[0]] = int(arg[1])

		self.TYPE = self.DEFAULT

		# Upper and lower limits cause "single" calculations
		if not self.F_LOWER_LIMIT <= options[0] <= self.F_UPPER_LIMIT or not self.D_LOWER_LIMIT <= options[1] <= self.D_UPPER_LIMIT:
			self.TYPE = self.SINGLE

		import random

		if self.TYPE == self.MULTIPLE:
			numbers = []

			# Get the numbers
			for each in range(options[1]):
				num = random.randint(self.F_LOWER_LIMIT, options[0])
				numbers += [num]

			# Give the results
			self.bot.privmsg(msg.channel, '%s: %r (total %d)' % (msg.nick, numbers, sum(numbers)))

		elif self.TYPE == self.SINGLE:
			# Just give the total
			total = random.randint(options[1] * self.F_LOWER_LIMIT, options[0] * options[1])

			# Give the results
			self.bot.privmsg(msg.channel, '%s: [...] (total %d)' % (msg.nick, total))
