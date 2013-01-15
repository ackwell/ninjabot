# Imports
import hashlib
import time

class Plugin:
	# Game statuses
	INACTIVE = 0
	LOBBY    = 1
	DAY      = 2
	NIGHT    = 3

	def __init__(self, bot, config):
		self.bot = bot
		self.config = config

		self.game_status = self.INACTIVE

		# Init variables nice n' empty
		self.town_channel = ""
		self.mafia_channel = ""
		self.players = []

	def trigger_mafia(self, msg):
		"Mafia: THAT'S MAFIA TALK! For a list of commands, run `mafia help`"
		if len(msg.args) == 0:
			self.bot.notice(msg.nick, "Please specify an Mafia command. Check `%smafia help` for avaliable commands."%self.bot.command_prefix)
			return

		command = msg.args.pop(0).lower()
		if 'mafia_'+command in dir(self):
			getattr(self, 'mafia_'+command)(msg)
		else:
			self.bot.notice(msg.nick, "The command '%s' does not exist. Check `%smafia help` for avalable commands."%(command, self.bot.command_prefix))
	
	def mafia_help(self, msg):
		self.bot.notice(msg.nick, "NOT IMPLEMENTED")

	def mafia_start(self, msg):
		# Check that there isn't a game running
		if self.game_status != self.INACTIVE:
			self.bot.notice(msg.nick, "There is already a game in play. Join %s if you would like to %sspectate" % (self.town_channel, "join or " if self.game_status == self.LOBBY else ""))

		# Create channels to play in (Need OP)
		channel_hash = hashlib.sha1(str(time.time())).hexdigest()[:8]
		self.town_channel = self.config['town_channel_name']+channel_hash
		self.mafia_channel = self.config['mafia_channel_name']+channel_hash
		self.bot.join(self.town_channel)
		self.bot.join(self.mafia_channel)
		# TODO: Regen hash, etc, if already users in channel

		# Hide the mafia channel
		self.bot.mode(self.mafia_channel, "+is")

		# Set game mode, announce game start
		self.game_status = self.LOBBY
		self.bot.privmsg(self.bot.config['bot']['channels'], "%s has started a game of Mafia! Join %s if you wish to join or spectate!" % (msg.nick, self.town_channel))

		# Set the lobby timeout
		self.bot.schedule(self._setup, self.config['lobby_timeout'])

	def _setup(self):
		pass