# This is an example plugin.

class Plugin:
	# All functions are optional. If a function doesn't exist, it simply won't be loaded.

	# This is the init for the plugin. All plugins are initiated when the bot is booted up.
	# The plugin will be re-initiated on reload and restart
	# It's probably a good idea to store a reference to the bot here, you'll need it
	# to utilise the bot's functions.
	# The plugin will also be passed a dictionary of it's config. More settings can be
	# accessed via bot.config
	def __init__(self, bot, config):
		self.bot = bot
		self.config = config

	# The on_incoming function is called every time a message is recieved by the bot.
	# This inclused PRIVMSG, NOTICE, etc.
	# If you wish to change the message, return the edited message object.
	def on_incoming(self, msg):
		return msg

	# Trigger responses can be defined by creating a function named trigger_<name>, where
	# <name> is an arbitary string. The trigger can then be called over IRC by the prefix
	# set in the config file, followed by <name>. For triggers, msg has an additional
	# property 'args', which is a dictonary of the arguments passed to it.
	def trigger_example(self, msg):
		"This docstring will be displayed by the help function"
		self.bot.privmsg(msg.channel, 'This is an example command response')

	# A timed function, defined by creating a function named timer_<time>, where <time> is
	# how often you want the function to be called (in seconds).
	def timer_10(self):
		self.bot.privmsg(self.bot.channel, 'Example of a timed function, executed every 10 seconds.')

# API reference:
# ninjabot doesn't have a full-on API, intead provididing all the functions in the ninjabot
# and parent classes. Below is a short listing of the more useful functions. For more info,
# take a look through ninjabot.py. The active instanc of the bot is passed to the __init__
# on load, use that reference for all calls.
#
# class Message
#   A Message instance will be passed to all non-timer event functions.
#
#	  channel, nick, host, body, ctcp
#	  	  Various vars set from the message data. Pretty self explanitory.
#
#	  args
#		  Only avaliable in trigger_ functions. Attempting to access it in other functions
#		  will cause your plugin to generate an error.
#		  A list of arguments to the trigger, omitting the trigger and prefix. I.E., for
#			  <prefix>example_trigger arg1 arg2 arg3
#		  msg.args would equate to
#			  ["arg1", "arg2", "arg3"]
#
# class ninjabot
#     is_admin (self, nickname, silent=False)
#	      Checks if nickname is an admin.
#	      If silent is False, a NOTICE will be sent to nick informing they do not meet the
#	      access level restriction. This setting is overidden by
#       config->bot->notify_insufficient_privs
#	      The various access level lists are maintained my Pugins/authtools.py
#
#	  notice(self, targets, message)
#   privmsg(self, targets, message)
#		  Sends an IRC NOTICE/PRIVMSG to targets, containing message and CTCP ctcp.
#		  target can be a nick or channel, and may be either a string, or a list of strings.
#
#	  config
#		  A dictionary containing the config file loaded by the bot on startup.
#
