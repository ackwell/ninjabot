# git plugin
# allows 'git pull' to be run remotely

from apis import git
import time

class Plugin:
    def __init__(self, controller):
        self.controller = controller
        self.git = git.Git()

    def trigger_gitpull(self, msg):
        if self.controller.is_admin(msg.nick):
            self.controller.notice(msg.nick, 'Running git pull...')
            response = self.git.pull()
            for line in response.split('\n'):
                self.controller.notice(msg.nick, line)
                time.sleep(0.2)
            self.controller.notice(msg.nick, 'Done!')
