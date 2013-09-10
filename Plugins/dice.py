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
		dice [<sides>d<num>]
		"""

		# Too many arguments
		if len(msg.args) > 1:
			self.bot.notice(msg.nick, 'Invalid number of arguments.')
			return

		# Default options
		sides, die = 6, 1

		# Convert args to options
		if len(msg.args) == 1:

			if len(msg.args[0].split('d')) != 2:
				self.bot.notice(msg.nick, 'Invalid argument %s' % msg.args[0])

			sides, die = msg.args[0].split('d')

			if not sides.isnumeric() or not die.isnumeric():
				self.bot.notice(msg.nick, 'Invalid argument %s' % msg.args[0])

			sides, die = int(sides), int(die)


		self.TYPE = self.DEFAULT

		# Upper and lower limits cause "single" calculations
		if not self.F_LOWER_LIMIT <= sides <= self.F_UPPER_LIMIT or not self.D_LOWER_LIMIT <= die <= self.D_UPPER_LIMIT:
			self.TYPE = self.SINGLE

		import random

		if self.TYPE == self.MULTIPLE:
			numbers = []

			# Get the numbers
			for each in range(die):
				num = random.randint(self.F_LOWER_LIMIT, sides)
				numbers += [num]

			# Give the results
			self.bot.privmsg(msg.channel, '%s: %s (total %d)' % (msg.nick, numbers, sum(numbers)))

		elif self.TYPE == self.SINGLE:
			# Just give the total
			total = random.randint(die * self.F_LOWER_LIMIT, sides * die)

			# Give the results
			self.bot.privmsg(msg.channel, '%s: [...] (total %d)' % (msg.nick, total))
