# This is an example plugin.

class Plugin:
	# Whether or not the plugin should be loaded. If not specified, assumed to be True
	active = False

	# All functions are optional. If a function doesn't exist, it simply won't be loaded.

	# This is the init for the plugin. All plugins are initiated when the bot is booted up.
	# The plugin will be re-initiated on reload and restart
	# It's probably a good idea to store a reference to the controller here, you'll need it
	# to utilise the bot's functions.
	def __init__(self, controller):
		self.controller = controller

	# The on_incoming function is called every time a message is recieved by the bot.
	# This inclused PRIVMSG, NOTICE, etc.
	# If you wish to change the message, return the edited message object.
	def on_incoming(self, msg):
		return msg

	# Much the same as on_incoming, but called with any message the bot sends.
	def on_outgoing(self, msg):
		return msg

	# Trigger responses can be defined by creating a function named trigger_<name>, where
	# <name> is an arbitary string. The trigger can then be called over IRC by the prefix
	# set in the config file, followed by <name>. For triggers, msg has an additional
	# property 'args', which is a dictonary of the arguments passed to it.
	def trigger_example(self, msg):
		"This docstring will be displayed by the help function"
		self.controller.privmsg(msg.channel, 'This is an example command response')

	# A timed function, defined by creating a function named timer_<time>, where <time> is
	# how often you want the function to be called (in seconds).
	def timer_10(self):
		self.controller.privmsg(self.controller.channel, 'Example of a timed function, executed every 10 seconds.')

# API reference:
# ninjabot doesn't have a real 'API', as such, however the Controller and Message classes
# provides most of the functionality you will need. Below is a short listing of the more
# useful functions. For more info, you'll want to take a look through the Controller class
# in Main.py, and the various classes it depends on. The instance of Controller is passed
# to the __init__ on load, use that reference for all calls.
#
# class Message
#	  A Message instance will be passed to all non-timer event functions.
#
#	  channel, nick, host, body, ctcp
#		  Various vars set from the message data. Pretty self explanitory.
#
#	  args
#		  Only avaliable in trigger_ functions. Attempting to access it in other functions
#		  will cause your plugin to generate an error.
#		  A list of arguments to the trigger, omitting the trigger and prefix. I.E., for
#			  <prefix>example_trigger arg1 arg2 arg3
#		  msg.args would equate to
#			  ["arg1", "arg2", "arg3"]
#
# class Controller
#     is_admin, is_op, is_voiced (self, nick, announce=True)
#	      Checks if nick meets the priliage specified. Note that the levels are inclusive
#	      of those above them, so bot OPs and admins will return True for is_voiced.
#	      If announce is True, a NOTICE will be sent to nick informing they do not meet the
#	      access level restriction.
#	      The various access level lists are maintained my Pugins/authtools.py
#	  
#	  is_ignored(self, nick)
#		  Returns True if the nick is on the ignored list, else False.
#	
#	  notice(self, target, message, ctcp='')
#		  Sends an IRC NOTICE to target, containing message and CTCP ctcp.
#		  target can be a nick or channel
#
#	  privmsg(self, target, message, ctcp='', ignore_plugins=False)
#		  Sends an IRC PRIVMSG to target, containing message and CTCP ctcp.
#		  target can be a nick or channel. If ignore_plugins is True, the message
#		  will bypass the plugin system.
#
#	  config
#		  A dictionary containing the config file loaded by the bot on startup.
#	  
#	  channel
#		  The default channel, specified in the config.
#
# class PluginHandler
#	  You can access the current instance of this with controller.plugins
#
#	  prefix
#		  A string containing the bot's trigger prefix
