'''
Regex replace plugin for ninjabot (https://github.com/ackwell/ninjabot/).
Watches incoming messages for sed substitution strings.
Supports using any-character separator if <prefix>sed is used.

Config:
"misc.regex": {
	"backlog": (int) /* Number of messages to retain for each user. Defaults to 5. */
}
'''

from collections import defaultdict as ddict, deque
import re


class Plugin(object):
	def __init__(self, bot, config):
		self.bot = bot

		self.last_messages = ddict(deque)

		# Keep this many past messages saved for each user
		self.backlog = 5
		if 'backlog' in config:
			self.backlog = config['backlog']

	def on_incoming(self, msg):
		# Only accept messages over the channel
		if msg.type == msg.CHANNEL:
			self._sed(msg, False)

	def trigger_sed(self, msg):
		# Need to strip the 'sed ' from the beginning of the message
		# (It'll always be there)
		msg.body = msg.body[4:]
		self._sed(msg, True)

	def _sed(self, msg, any_seperator):
		# TODO: This code **needs** to be fixed. Consider looking at the source
		#       code of GNU sed or other tools for ideas. Regex should *not* be
		#       used for parsing. Use something more sane and measured.
		#       - Cyphar

		# Check if the message matches the s/blah/blah/ syntax
		regex = r'''(?x)  # verbose mode
			^(s|y|tr)(SEPARATOR) # starts with the mode, then our separator
			((?:  # capture pattern
				(?:\\\2)*        # any number of escaped separators
				(?:(?!\2).)      # a non-sep
			)+?)  # ...as many times as possible, end capture pattern
			\2                   # separator
			((?:
				(?:\\\2)*
				(?:(?!\2).)
			)*?)
			(?:\2([g0-9])?)?$    # end with optional separator with optional flags
		'''.replace('SEPARATOR', r'.' if any_seperator else r'\W')

		matches = re.match(regex, msg.body)
		if matches:
			groups = matches.groups()
			body = ''

			# Did they have a last message?
			if msg.nick in self.last_messages:
				their_messages = self.last_messages[msg.nick]
				mode, sep, pattern, replacement, flags = [s.replace('\\'+groups[1], groups[1]) if s else '' for s in groups]

				if mode == 's':  # String replace mode
					# Scan for a matching message in their last messages
					for message in their_messages:
						try:  # Treat the rexes as a normal message if an error occurs, i.e. invalid syntax
							if re.search(pattern, message):
								if 'g' in flags:
									body = re.sub(pattern, replacement, message)
								elif flags.isdigit():
									flags = int(flags)
									matches = list(re.finditer(pattern, message))
									if len(matches) >= flags:
										span = matches[flags-1].span()
										body = message[:span[0]] + replacement + message[span[1]:]
									else:
										return
								else:
									body = re.sub(pattern, replacement, message, 1)

								# Send it
								if not len(body):
									self.bot.privmsg(msg.channel, msg.nick + ' said nothing.')
								else:
									self.bot.privmsg(msg.channel, '{0} meant to say: {1}'.format(msg.nick, body))

								break
						except:
							pass
					else:
						# Match wasn't found, return without adding to last messages
						return
				elif mode == 'tr' or mode == 'y':
					if pattern and replacement and len(pattern) == len(replacement):
						last_message = their_messages[0]
						body = last_message.translate(dict(zip(map(ord, pattern), replacement)))
						self.bot.privmsg(msg.channel, '{0}: {1}'.format(msg.nick, body))
					else:
						# Was invalid, return without adding to last messages
						return

		# Add it to the last messages dictionary
		their_messages = self.last_messages[msg.nick]
		their_messages.appendleft(msg.body)
		if len(their_messages) > self.backlog:
			their_messages.pop()
