import os.path
import platform
import time

SOURCE = 'SOURCE https://github.com/ackwell/ninjabot'

class Plugin:
    def __init__(self, bot, config):
        self.bot = bot
        self.git = self.bot.request_api('git').Git()

    def on_incoming(self, msg):
        if not msg.ctcp: return

        args = msg.ctcp.split()
        command = args.pop(0).lower()

        if command == 'version':
            revision = self.git.current_revision()
            if not revision:
                revision = '<unknown>'
            version = '{0} ({1})'.format(self.bot.VERSION, revision)
            python_info = 'Python ' + platform.python_version()
            platform_info = platform.platform()
            node_info = platform.node()
            self.bot.notice(msg.nick, '\x01VERSION ninjabot {0}, running on {1}, {2}, {3}\x01'.format(version, node_info, python_info, platform_info))

        if command == 'source':
            src = SOURCE
            self.bot.notice(msg.nick, '\x01SOURCE {0}\x01'.format(src))

        elif command == 'time':
            self.bot.notice(msg.nick, '\x01TIME {0}\x01'.format(time.ctime()))

        elif command == 'ping':
            self.bot.notice(msg.nick, '\x01PING {0}\x01'.format(' '.join(args)))

        elif command == 'prefix':
            self.bot.notice(msg.nick, '\x01PREFIX {0}\x01'.format(self.bot.command_prefix))
