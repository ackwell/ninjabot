from apis import git
import os.path
import platform

SOURCE = 'SOURCE https://github.com/AClockWorkLemon/NCSSBot'

class Plugin:
    def __init__(self, controller):
        self.c = controller
        self.git = git.Git(path=os.path.join(['..', '..', '.git']))

    def on_incoming(self, msg):
        if not msg.ctcp: return msg

        args = msg.ctcp.split()
        command = args.pop(0).lower()

        if command == 'version':
            mode = ('GUI' if self.c.gui.graphical else 'CLI')
            revision = self.git.current_revision()
            if not revision:
                revision = '<unknown>'
            python_info = 'Python %s' % platform.python_version()
            platform_info = platform.platform()
            node_info = platform.node()
            self.c.notice(msg.nick, 'NCSSBot revision %s, running on %s in %s mode, %s, %s' % (revision, node_info, mode, python_info, platform_info))
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
