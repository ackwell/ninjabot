from apis import git
import os.path
import platform
import time

SOURCE = 'SOURCE https://github.com/ackwell/ninjabot'

class Plugin:
    def __init__(self, controller, config):
        self.c = controller
        self.git = git.Git()

    def on_incoming(self, msg):
        if not msg.ctcp: return

        args = msg.ctcp.split()
        command = args.pop(0).lower()

        if command == 'version':
            revision = self.git.current_revision()
            if not revision:
                revision = '<unknown>'
            python_info = 'Python %s' % platform.python_version()
            platform_info = platform.platform()
            node_info = platform.node()
            self.c.notice(msg.nick, '\x01VERSION ninjabot revision %s, running on %s, %s, %s\x01' % (revision, node_info, python_info, platform_info))

        elif command == 'source':
            src = SOURCE
            self.c.notice(msg.nick, '\x01%s\x01' % src)

        elif command == 'time':
            self.c.notice(msg.nick, '\x01TIME %s\x01' % time.ctime())

        elif command == 'ping':
            self.c.notice(msg.nick, '\x01PING %s\x01' % ' '.join(args))
