from apis import git
import os.path
import platform
import time

SOURCE = 'SOURCE https://github.com/ackwell/ninjabot'

class Plugin:
    def __init__(self, controller):
        self.c = controller
        self.git = git.Git()

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
            self.c.notice(msg.nick, '\x01VERSION NCSSBot revision %s, running on %s in %s mode, %s, %s\x01' % (revision, node_info, mode, python_info, platform_info))
            msg.body += 'Recieved CTCP VERSION from '+msg.nick
            msg.nick = '*'
            msg.ctcp = ''

        elif command == 'source':
            revision = self.git.current_revision()
            if revision:
                src = SOURCE + '/commit/' + revision
            else:
                src = SOURCE
            self.c.notice(msg.nick, '\x01%s\x01' % src)
            msg.body += 'Recieved CTCP SOURCE from '+msg.nick
            msg.nick = '*'
            msg.ctcp = ''

        elif command == 'time':
            self.c.notice(msg.nick, '\x01TIME %s\x01' % time.ctime())
            msg.body += 'Received CTCP TIME from '+msg.nick
            msg.nick = '*'
            msg.ctcp = ''

        elif command == 'ping':
            self.c.notice(msg.nick, '\x01PING %s\x01' % ' '.join(args))
            msg.body += 'Received CTCP PING from '+msg.nick
            msg.nick = '*'
            msg.ctcp = ''

        elif command == 'action':
            msg.body = msg.nick+' '+' '.join(args)
            msg.nick = '*'
            msg.ctcp = ''

        return msg
