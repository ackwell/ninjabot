VERSION = 'VERSION NCSSBot Dev0.3 '
SOURCE = 'SOURCE https://github.com/AClockWorkLemon/NCSSBot'

class Plugin:
	def __init__(self, controller):
		self.controller = controller

	def on_incoming(self, msg):
		if not msg.ctcp: return msg

		args = msg.ctcp.split()
		command = args.pop(0).lower()

		if command == 'version':
			self.controller.notice(msg.nick, VERSION+('GUI' if self.controller.gui.graphical else 'CLI')+' Mode')
		elif command == 'source':
			self.controller.notice(msg.nick, SOURCE)

		return msg

	def trigger_test(self, msg):
		self.controller.privmsg(msg.channel, 'This is a test message.')