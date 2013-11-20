# git plugin
# allows 'git pull' to be run remotely

import subprocess
import time


class Plugin(object):
	def load(self, bot, config):
		self.bot = bot
		self.git = self.bot.request_api('core.git')()

	def trigger_gitpull(self, msg):
		if self.bot.is_admin(msg.nick):
			self.bot.notice(msg.nick, "Running git pull...")
			response = self.git.pull()
			for line in response.split('\n'):
				self.bot.notice(msg.nick, line)
				time.sleep(0.2)
			self.bot.notice(msg.nick, "Done!")


# API for the above plugin
class Git(object):
	def __init__(self):
		pass

	def pull(self):
		return self._cli_command('git pull')

	def current_revision(self):
		return self._cli_command('git rev-list HEAD -n 1');

	def _cli_command(self, command):
		response = subprocess.check_output(command.split()).decode('utf-8')
		return response.strip()


APIS = {
	'core.git': Git
}
