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
			msg.body += 'Recieved CTCP VERSION from '+msg.nick
			msg.nick = '*'
			msg.ctcp = ''
			self.controller.notice(msg.nick, VERSION+('GUI' if self.controller.gui.graphical else 'CLI')+' Mode')
		elif command == 'source':
			msg.body += 'Recieved CTCP SOURCE from '+msg.nick
			msg.nick = '*'
			msg.ctcp = ''
			self.controller.notice(msg.nick, SOURCE)

		elif command == 'action':
			msg.body = msg.nick+' '+' '.join(args)
			msg.nick = '*'
			msg.ctcp = ''

		return msg