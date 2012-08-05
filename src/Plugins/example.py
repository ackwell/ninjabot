# This is an example plugin.

class Plugin:
	# This is the init for the plugin. All plugins are initiated when the bot is booted up.
	# If/when I implement a reload function, plugins would be re-initiated when reloaded.
	# It's probably a good idea to store a reference to the controller here, 
	# You'll need it to utilise the bot's functions.
	def __init__(self, controller):
		self.controller = controller

	# The on_incoming function is called every time a message is recieved by the bot.
	# This inclused PRIVMSG, NOTICE, etc. It MUST return msg (you can change it, of course),
	# else the bot will throw a hissy. (I should probably fix this).
	def on_incoming(self, msg):
		return msg

	# Much the same as on_incoming, but called with any message the bot sends
	def on_outgoing(self, msg):
		return msg

	# Trigger responses can be defined by creating a function named trigger_<name>, where
	# <name> is an arbitary string. The trigger can then be called over IRC by the prefix
	# set in the PluginHandler (I really need to make a config file -_-), followed by <name>
	# For triggers, msg has an additional property 'args', which is a dictonary of the
	# arguments passed to it
	def trigger_example(self, msg):
		self.controller.privmsg(msg.channel, 'This is an example command response')