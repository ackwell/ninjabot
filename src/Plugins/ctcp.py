VERSION = 'VERSION NCSSBot Dev0.3 '
SOURCE = 'SOURCE https://github.com/AClockWorkLemon/NCSSBot'

class Plugin:
	def __init__(self, controller):
		self.c = controller

	def on_incoming(self, msg):
		if not msg.ctcp: return msg

		args = msg.ctcp.split()
		command = args.pop(0).lower()

		if command == 'version':
			self.c.notice(msg.nick, VERSION+('GUI' if self.c.gui.graphical else 'CLI')+' Mode')
			msg.body += 'Recieved CTCP VERSION from '+msg.nick
			msg.nick = '*'
			msg.ctcp = ''
		
		elif command == 'source':
			self.c.notice(msg.nick, SOURCE)
			msg.body += 'Recieved CTCP SOURCE from '+msg.nick
			msg.nick = '*'
			msg.ctcp = ''

		elif command == 'action':
			msg.body = msg.nick+' '+' '.join(args)
			msg.nick = '*'
			msg.ctcp = ''

		return msg