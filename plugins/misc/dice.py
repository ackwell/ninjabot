# Dice plugin
# Written by Cyphar
# Do whatever you want with this.
import random
import math

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

	def load(self, bot, config):
		self.bot = bot
		self.config = config

	def dice_random(self, num, size):
		"""Gives a nice normal distribution for dice"""
		sigma = math.sqrt(num * (size**2 - 1) / 12)
		mean = num * (size + 1) / 2

		return int(random.gauss(mean, sigma))

	def trigger_dice(self, msg):
		"Roll a die (or dice), using the <num>d<faces> syntax."

		# Too many arguments
		if len(msg.args) > 1:
			self.bot.notice(msg.nick, 'Invalid number of arguments.')
			return

		# Default options
		sides, die = 6, 1

		# Convert args to options
		if len(msg.args) == 1:

			if "d" in msg.args[0]:
				if len(msg.args[0].split('d')) != 2:
					self.bot.notice(msg.nick, 'Invalid argument {:s}'.format(msg.args[0]))
					return

				die, sides = msg.args[0].split('d')

				if not die:
					die = "1"

				if not sides.isnumeric() or not die.isnumeric():
					self.bot.notice(msg.nick, 'Invalid argument {:s}'.format(msg.args[0]))
					return

			elif msg.args[0].isnumeric():
				die = int(msg.args[0])

			else:
				self.bot.notice(msg.nick, 'Invalid argument {:s}'.format(msg.args[0]))
				return

			sides, die = int(sides), int(die)

		self.TYPE = self.DEFAULT

		# Lower limits cause errors
		if self.F_LOWER_LIMIT > sides or self.D_LOWER_LIMIT > die:
			self.bot.notice(msg.nick, 'Invalid argument {:s}'.format(msg.args[0]))
			return

		# Upper limits cause "single" calculations
		if sides > self.F_UPPER_LIMIT or die > self.D_UPPER_LIMIT:
			self.TYPE = self.SINGLE

		if self.TYPE == self.MULTIPLE:
			numbers = []

			# Get the numbers
			for each in range(die):
				num = random.randint(self.F_LOWER_LIMIT, sides)
				numbers += [num]

			# Give the results
			self.bot.privmsg(msg.channel, '{:s}: {:s} (total {:d})'.format(msg.nick, numbers, sum(numbers)))

		elif self.TYPE == self.SINGLE:
			# Since random.* are expensive operations, treat the whole thing as one gargantuan die
			# btw -- dice_random() gives a normal distribution, making the output more 'realistic'.
			total = self.dice_random(die, sides)

			# Give the results
			self.bot.privmsg(msg.channel, '{:s}: [...] (total {:d})'.format(msg.nick, total))
