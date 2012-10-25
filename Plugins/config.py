# Plugin to allow editing of the config at runtime
import json

class Plugin:
	def __init__(self, bot, config):
		self.bot = bot

	def trigger_config(self, msg):
		"Runtime config editing. for more info, check `config help`"
		if not self.bot.is_admin(msg.nick): return

		if len(msg.args) == 0:
			self.bot.notice(msg.nick, "No command specified.")
			return

		command = msg.args.pop(0).lower()
		if 'config_'+command in dir(self):
			getattr(self, 'config_'+command)(msg)
		else:
			self.bot.notice(msg.nick, "The command '%s' does not exist. Check `%sconfig help` for avalable commands."%(command, self.c.command_prefix))

	def config_help(self, msg):
		self.bot.notice(msg.nick, "%sconfig set p1 [p2 ...] value: Sets the config path specified to value."%self.bot.command_prefix)
		self.bot.notice(msg.nick, "%sconfig get p1 [p2 ...]: Retrieves value for specified config path."%self.bot.command_prefix)
		self.bot.notice(msg.nick, "%sconfig save: Saves the current config to file."%self.bot.command_prefix)

	def config_set(self, msg):
		config = self._get_config(msg.args[:-2])
		config[msg.args[-2]] = eval(msg.args[-1])
		self.bot.notice(msg.nick, "Setting changed sucessfully")

	def config_get(self, msg):
		config = self._get_config(msg.args[:], create=False)
		if config:
			self.bot.notice(msg.nick, "'%s' is currently set to '%s'" % ('->'.join(msg.args), str(config)))
		else:
			self.bot.notice(msg.nick, "Config path '%s' is not currently set."%'->'.join(msg.args))

	def config_save(self, msg):
		f_config = open(self.bot.config_path, 'w')
		f_config.write(json.dumps(self.bot.config, indent=2))
		f_config.close()
		self.bot.notice(msg.nick, "Config saved sucessfully.")

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