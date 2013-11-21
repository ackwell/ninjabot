# Plugin to allow editing of the config at runtime
import json


class Plugin(object):
	def load(self, bot, config):
		self.bot = bot

	def trigger_config(self, msg):
		"Runtime config editing. For more info, check `config help`"
		if not self.bot.is_admin(msg.nick):
			return

		if len(msg.args) == 0:
			self.bot.notice(msg.nick, "No command specified.")
			return

		command = msg.args.pop(0).lower()
		if 'config_'+command in dir(self):
			getattr(self, 'config_'+command)(msg)
		else:
			self.bot.notice(msg.nick, "The command '{0}' does not exist. Check `{1}config help` for available commands.".format(command, self.bot.command_prefix))

	def config_help(self, msg):
		self.bot.notice(msg.nick, "{0}config set p1 [p2 ...] value: Sets the config path specified to value.".format(self.bot.command_prefix))
		self.bot.notice(msg.nick, "{0}config get p1 [p2 ...]: Retrieves value for specified config path.".format(self.bot.command_prefix))
		self.bot.notice(msg.nick, "{0}config save: Saves the current config to file.".format(self.bot.command_prefix))

	def config_set(self, msg):
		config = self._get_config(msg.args[:-2])
		config[msg.args[-2]] = eval(msg.args[-1])
		self.bot.notice(msg.nick, "Setting changed successfully")

	def config_append(self, msg):
		config = self._get_config(msg.args[:-1])
		if not isinstance(config, list):
			self.bot.notice(msg.nick, "Trying to append to non-list item. Aborted.")
			return
		config.append(msg.args[-1])
		self.bot.notice(msg.nick, "Setting updated successfully")

	def config_remove(self, msg):
		config = self._get_config(msg.args[:-1])
		if not isinstance(config, list):
			self.bot.notice(msg.nick, "Trying to remove from non-list item. Aborting.")
			return
		to_remove = msg.args[-1]
		if to_remove not in config:
			self.bot.notice(msg.nick, "Value to be removed is not in specified item. Aborting.")
			return
		config.remove(msg.args[-1])
		self.bot.notice(msg.nick, "Setting updated successfully")

	def config_get(self, msg):
		config = self._get_config(msg.args[:], create=False)
		if config:
			self.bot.notice(msg.nick, "'{0}' is currently set to '{1}'".format('->'.join(msg.args), str(config)))
		else:
			self.bot.notice(msg.nick, "Config path '{0}' is not currently set.".format('->'.join(msg.args)))

	def config_save(self, msg):
		with open(self.bot.config_path, 'w') as f_config:
			f_config.write(json.dumps(self.bot.config, indent=2))

		self.bot.notice(msg.nick, "Config saved successfully.")

	def _get_config(self, path, create=True):
		config = self.bot.config
		while len(path):
			key = path.pop(0)
			if key not in config:
				if create:
					config[key] = {}
				else:
					return False
			config = config[key]
		return config
