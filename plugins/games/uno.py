'''
Port of the card game UNO!, for IRC. Because its fun, and why not.
All the commands used to play are sub-commands of <prefix>uno

Config:
"games.uno": {
	"join_phase": (float), /* Time (in minutes) the join phase lasts for. Defaults to 2. */
	"cooldown": (float), /* Time (in minutes) the game cooldown lasts for. Defaults to 10.*/
	"announce_cooldown": (boolean) /* Whether or not the bot should announce when cooldown is over. Defaults to true. */
}
'''

import random
from collections import defaultdict


class Plugin:

	#modes
	INACTIVE = 0
	JOINING = 1
	PLAYING = 2
	COOLDOWN = 3

	#player direction
	FORWARD = 1
	BACKWARD = -1

	def load(self, bot, config):
		self.bot = bot

		# Config
		self.join_phase_time = 2
		if 'join_phase' in config:
			self.join_phase_time = config['join_phase']
		self.cooldown_time = 10
		if 'cooldown' in config:
			self.cooldown_time = config['cooldown']
		self.announce_cooldown = True
		if 'announce_cooldown' in config:
			self.announce_cooldown = config['announce_cooldown']

		self.uno = "\002\0034U\0033N\0032O\0038!\003\002"

		# Create full deck
		self.full_deck = [colour+card for colour in 'rgby' for card in '123456789RSD'*2+'0']
		self.full_deck += ['wW', 'wW4']*4

		self.deck = []
		self.hands = defaultdict(list)
		self.discard = []

		self.schedule_task = None
		self.mode = self.INACTIVE
		self.turn = 0

		self.current_player = 0
		self.last_player = 0
		self.players = []
		self.start_player = ''
		self.channel = ''

		self.direction = self.FORWARD
		self._skip = 0
		self.force_colour = False
		self.topcolour = ''
		self.topnumber = -1

		# list of colourblind players
		self.colourblind_players = []

	def trigger_uno(self, msg):
		"\002\0034U\0033N\0032O\0038!\003:\002 Uno for IRC. For detailed help, run `uno help`"

		if len(msg.args) == 0:
			self.bot.notice(msg.nick, "Please specify an UNO command. Check `{}uno help` for available commands.".format(self.bot.command_prefix))
			return

		command = msg.args.pop(0).lower()
		if 'uno_'+command in dir(self):
			getattr(self, 'uno_'+command)(msg)
		else:
			self.bot.notice(msg.nick, "The command '{}' does not exist. Check `{}uno help` for available commands.".format(command, self.bot.command_prefix))

	def on_incoming(self, msg):
		"Check for nick changes"
		if msg.command == 'NICK' and msg.nick in self.players:
			self.players[self.players.index(msg.nick)] = msg.body
			if msg.nick in self.hands:
				self.hands[msg.body] = self.hands[msg.nick]
				del self.hands[msg.nick]

	def uno_help(self, msg):
		"Prints the help text. Further command help can be displayed by specifying a command."
		if len(msg.args) == 0:
			self.bot.notice(msg.nick, '{} is an IRC implementation of the popular card game of the same name.'.format(self.uno))
			com = []
			for d in dir(self):
				if d.startswith('uno_'):
					com.append(d.split('_')[1])
			self.bot.notice(msg.nick, 'Available sub-commands are: {}.'.format(' '.join(com)))
			self.bot.notice(msg.nick, 'For more information, run `{}uno help <command>`.'.format(self.bot.command_prefix))
		else:
			try:
				self.bot.notice(msg.nick, getattr(self, 'uno_'+msg.args[0]).__doc__)
			except AttributeError:
				self.bot.notice(msg.nick, "That command does not exist. For a list of commands, run {}uno help.".format(self.bot.command_prefix))

	def uno_start(self, msg):
		"Starts a game of UNO!"
		# Can't-play conditions...
		if self.mode == self.COOLDOWN:
			self.bot.notice(msg.nick, "{} is on cooldown. Try again later.".format(self.uno))
			return
		if self.mode:
			self.bot.notice(msg.nick, "There is already a game of {} running!".format(self.uno))
			return

		self.mode = self.JOINING
		self.start_player = msg.nick
		self.channel = msg.channel
		self.bot.privmsg(self.channel, "New game of {} starting! Type `{}uno join` to join the fun! Game will start in {} minute{}...".format(self.uno, self.bot.command_prefix, self.join_phase_time, '' if self.join_phase_time == 1 else 's'))
		self.uno_join(msg)

		# Schedule the end of the join phase
		self.schedule_task = self.bot.schedule(self.join_phase_time*60, self._begin)

		# Clear the colourblind list
		self.colourblind_players = []

	def uno_stop(self, msg):
		"Stops the current game of UNO!. Only admins and the start player can stop a game."
		if not (self.bot.is_admin(msg.nick, True) or msg.nick == self.start_player):
			self.bot.notice(msg.nick, "Only ops+ and the start player can stop a game.")
			return
		elif self.mode == self.INACTIVE:
			self.bot.notice(msg.nick, "There is no game of {} in progress.".format(self.uno))
			return

		self._reset()

	def uno_join(self, msg):
		"Join a running game of uno. Only available during the joining phase."
		if msg.channel != self.channel:
			self.bot.notice(msg.nick, "Please join {} to join the game of {}.".format(self.channel, self.uno))
			return
		elif msg.nick in self.players:
			self.bot.notice(msg.nick, "You've already joined the game!")
			return
		elif len(self.players) == 10:
			self.bot.notice(msg.nick, "The current game of {} is full, sorry.".format(self.uno))
			return
		elif self.mode == self.INACTIVE:
			self.bot.notice(msg.nick, 'There is no {} game running! Why not start one with `{}uno start`?'.format(self.uno, self.bot.command_prefix))
			return
		elif self.mode == self.PLAYING:
			self.bot.notice(msg.nick, "There's already a game of {} running!".format(self.uno))
			return

		self.players.append(msg.nick)
		self.bot.privmsg(self.channel, "{} has joined the game!".format(msg.nick))
		if len(self.players) == 10:
			self.bot.privmsg(self.channel, "The game is full! Get ready to play {}!".format(self.uno))
			self.bot.cancel_schedule(self.schedule_task)
			self.schedule_task = None
			self._begin()

	def uno_leave(self, msg):
		"Leave the game."
		if self.mode == self.PLAYING:
			if len(msg.args) == 0:
				self.bot.notice(msg.nick, "Please confirm you wish to leave with `{}uno leave confirm`.".format(self.bot.command_prefix))
				return
			elif msg.args[0].lower() != 'confirm':
				return
		elif msg.nick not in self.players:
			self.bot.notice(msg.nick, "You can't leave something you haven't joined!")
			return

		self.bot.privmsg(self.channel, "{} has left the game.".format(msg.nick))
		self._remove(msg.nick)

	def uno_kick(self, msg):
		"Kicks a player from the game."
		if not self.bot.is_admin(msg.nick):
			return
		elif self.mode != self.PLAYING:
			self.bot.notice(msg.nick, "There is no game in progress.")
			return
		elif len(msg.args) == 0:
			self.bot.notice(msg.nick, "Please specify a person to kick.")
			return
		elif msg.args[0] not in self.players:
			self.bot.notice(msg.nick, "There is no player with that nick.")
			return

		self.bot.privmsg(self.channel, "{} has kicked {} from the game.".format(msg.nick, msg.args[0]))
		self._remove(msg.args[0])

	def _remove(self, nick):
		next = True if self.mode == self.PLAYING and self.players[self.current_player] == nick else False
		if self.players.index(nick) <= self.current_player:
			self.current_player -= 1
		self.players.remove(nick)

		if self.mode == self.PLAYING:
			self.bot.privmsg(self.channel, "Their hand was {}. It has been shuffled into the deck.".format(self._render_hand(nick, colourblind=False)))
			for card in self.hands[nick]:
				self.deck.insert(random.randint(0, len(self.deck)), card)

			del self.hands[nick]
		if next:
			self._begin_turn()

	CARD_MAP = {
		'draw': 'D',
		'skip': 'S',
		'reverse': 'R',
		'wild': 'W',
		'wild4': 'W4',
		'wildfour': 'W4',
		'red': 'r',
		'green': 'g',
		'blue': 'b',
		'yellow': 'y'
	}
	NAME_MAP = {
		'W': 'Wild',
		'W4': 'Wild Draw Four',
		'R': 'Reverse',
		'S': 'Skip',
		'D': 'Draw Two',
		'r': 'Red',
		'g': 'Green',
		'b': 'Blue',
		'y': 'Yellow'
	}

	def uno_play(self, msg):
		"Play a card. syntax is `play <colour> <card>. For wilds, specify a colour they should become."
		if not self.mode == self.PLAYING:
			self.bot.notice(msg.nick, "There's no game of {} currently in progress!".format(self.uno))
			return

		if not self.players[self.current_player] == msg.nick:
			self.bot.notice(msg.nick, "It's not your turn!")
			return

		if len(msg.args) == 0:
			self.bot.notice(msg.nick, "Not enough arguments specified.")
			return

		colour = msg.args.pop(0).lower()
		try:
			colour = self.CARD_MAP[colour]
		except KeyError:
			pass

		if colour not in 'rgby':
			self.bot.notice(msg.nick, "Invalid colour specified.")
			return

		if self.force_colour and colour != self.topcolour:
			if self.turn != 1:
				self.bot.notice(msg.nick, "You must place a {} card, or pick up.".format(self.NAME_MAP[self.topcolour]))
				return
		elif self.force_colour:
			self.force_colour = False

		ctype = "".join(msg.args).lower()
		try:
			ctype = self.CARD_MAP[ctype]
		except KeyError:
			pass

		ctype = ctype.upper()
		if ctype not in 'RSDW4012356789':
			self.bot.notice(msg.nick, "Invalid card type specified.")
			return

		card = ('w' if (ctype == 'W' or ctype == 'W4') else colour)+ctype
		if card not in self.hands[msg.nick]:
			self.bot.notice(msg.nick, "You do not have that card")
			return

		if not (ctype == self.topnumber or colour == self.topcolour or 'W' in ctype):
			self.bot.notice(msg.nick, "That card cannot be placed.")
			return

		if ctype == 'W4' and self.topcolour in [i[0] for i in self.hands[msg.nick]]:
			self.bot.notice(msg.nick, "Wild Draw Four cards can only be placed when you do not have a card the same colour as the pile.")
			return

		self.hands[msg.nick].remove(card)

		card = colour+ctype
		try:
			lname = self.NAME_MAP[ctype]
		except KeyError:
			lname = ctype

		self.bot.privmsg(self.channel, "{} plays a {} {}.".format(msg.nick, self.NAME_MAP[colour], lname))

		cards_left = len(self.hands[msg.nick])
		if cards_left == 1:
			self.bot.privmsg(self.channel, "{} {} has 1 card remaining!".format(self.uno, msg.nick))
		elif cards_left == 0:
			self.bot.privmsg(self.channel, "{} is out of cards! WINNER!~".format(msg.nick))
			self._reset()
			return

		self._do_action(card)
		self._discard(card)
		self._begin_turn()

	def uno_hand(self, msg):
		"Displays your current hand."
		if not msg.nick in self.players:
			self.bot.notice(msg.nick, "You are not playing!")
			return

		self.bot.notice(msg.nick, "Your hand: {}".format(self._render_hand(msg.nick)))

	def uno_top(self, msg):
		"Displays the current top card"
		if not self.mode == self.PLAYING:
			self.bot.notice(msg.nick, "There is no game in progress.")
			return

		self.bot.notice(msg.nick, "Top card: {}".format(self._render_card(self.discard[-1])))

	def uno_draw(self, msg):
		"Draw a card from the deck."
		self.uno_pickup(msg)

	def uno_pickup(self, msg):
		"Draw a card from the deck."
		if not self.players[self.current_player] == msg.nick:
			self.bot.notice(msg.nick, "It's not your turn!")
			return
		self._draw_card(msg.nick)
		self._begin_turn()

	def uno_colourblind(self, msg):
		"Toggles your colourblind status. When enabled, you can play the game without having colours enabled in your IRC client."
		player = msg.nick
		if player in self.players:
			if player in self.colourblind_players:
				self.colourblind_players.remove(player)
				self.bot.notice(player, "You are no longer set as colourblind.")
			else:
				self.colourblind_players.append(player)
				self.bot.notice(player, "You are now set as colourblind.")
		else:
			self.bot.notice(player, "You must be playing to toggle your colourblind status!")

	def uno_skip(self, msg):
		"Can be used to skip join and new game cooldowns."
		if self.mode == self.COOLDOWN:
			if self.bot.is_admin(msg.nick):
				self.bot.cancel_schedule(self.schedule_task)
				self.schedule_task = None
				if self.announce_cooldown:
					self.bot.privmsg(self.channel, "Cooldown skipped. {} is ready to play!".format(self.uno))
			return

		if not (self.bot.is_admin(msg.nick, True) or msg.nick == self.start_player):
			self.bot.notice(msg.nick, "Only bot admins and the start player can skip.")
			return

		if self.mode != self.JOINING:
			self.bot.notice(msg.nick, "This command can only be used in the player signup stage.")

		self.bot.cancel_schedule(self.schedule_task)
		self.schedule_task = None
		self._begin()

	def _begin(self):
		print('BEGIN')

		if len(self.players) < 2:
			self.bot.privmsg(self.channel, "{} needs at least 2 people to play! Game halted.".format(self.uno))
			self._reset(False)
			return

		self.mode = self.PLAYING
		self._set_up()

	def _reset(self, CD=True):
		# Clear schedules
		if self.schedule_task:
			self.bot.cancel_schedule(self.schedule_task)
			self.schedule_task = None

		self.players = []
		self.start_player = ''
		self.mode = self.COOLDOWN if CD and self.cooldown_time else self.INACTIVE
		self.turn = 0

		if self.mode == self.COOLDOWN:
			self.schedule_task = self.bot.schedule(self.cooldown_time * 60, self._cooldown_complete)
			self.bot.privmsg(self.channel, "{} game finished. Hope you had fun! Uno can be played again in about {} minute{}.".format(self.uno, self.cooldown_time, '' if self.cooldown_time == 1 else 's'))

	def _cooldown_complete(self):
		self.schedule_task = None
		self.mode = self.INACTIVE
		if self.announce_cooldown:
			self.bot.privmsg(self.channel, "Cooldown complete! {} is ready to play!".format(self.uno))

	# Set up the game!
	def _set_up(self):
		#Shuffle the cards and the player order (man python makes one's life easy :D)
		random.shuffle(self.players)
		self.deck = self.full_deck[:]
		random.shuffle(self.deck)

		self.bot.privmsg(self.channel, "{} is dealing.".format(self.players[self.current_player]))

		#Deal the cards. Gotta keep it going 'round the table, it's how it works!
		self.hands = defaultdict(list)
		for player in self.players * 7:  # 7 cards each
			self._draw_card(player, silent=True)

		#Start the discard pile
		self.bot.privmsg(self.channel, "Flipping the top card...")
		discard = self.deck.pop()
		while discard == 'wW4':  # first card can't be a Wild D4
			self.bot.privmsg(self.channel, "It was a \002Wild Draw Four\002. Flipping next card.")
			self.deck.insert(random.randint(0, len(self.deck)), 'wW4')
			discard = self.deck.pop()
		self._discard(discard)

		self._begin_turn()

	def _discard(self, card):
		self.discard.append(card)
		self.topcolour = card[0]
		self.topnumber = card[1:]

	def _begin_turn(self):
		self.last_player = self.current_player
		self._next_player()
		while self._skip > 0:
			self._skip -= 1
			self.bot.privmsg(self.channel, "{}'s turn was skipped.".format(self.players[self.current_player]))
			self._next_player()

		self.turn += 1

		lplayer = self.players[self.last_player]
		player = self.players[self.current_player]
		nplayer = self.players[self._next_player(True)]
		if self.direction == 1:
			turns = "{} ({}) ->\002 {} ({}) \002-> {} ({})".format(lplayer, len(self.hands[lplayer]), player, len(self.hands[player]), nplayer, len(self.hands[nplayer]))
		else:
			turns = "{} ({}) <-\002 {} ({}) \002<- {} ({})".format(nplayer, len(self.hands[nplayer]), player, len(self.hands[player]), lplayer, len(self.hands[lplayer]))

		self.bot.privmsg(self.channel, "Turn {}: {}".format(self.turn, turns))
		self.bot.privmsg(self.channel, "Top card: {}".format(self._render_card(self.discard[-1])))
		for p in self.colourblind_players:
			self.bot.notice(p, "Top card: {}".format(self._render_card(self.discard[-1], colourblind=True)))
		self.bot.notice(player, "Your hand: {}".format(self._render_hand(player)))

	def _next_player(self, get=False):
		temp = self.current_player
		self.current_player += self.direction
		if self.current_player < 0:
			self.current_player += len(self.players)
		elif self.current_player >= len(self.players):
			self.current_player -= len(self.players)
		if get:
			num = self.current_player
			self.current_player = temp
			return num

	def _do_action(self, card):
		card_type = card[1:]
		if card_type == 'R':
			if len(self.players) == 2:
				self._skip = 1
			else:
				self.direction = -self.direction
				self.bot.privmsg(self.channel, "Direction of play was reversed!")
		elif card_type == 'S':
			self._skip = 1
		elif card_type == 'D':
			self._draw_card(self.players[self._next_player(True)], 2)
			self._skip = 1
		elif card_type == 'W':
			self.force_colour = True
		elif card_type == 'W4':
			self._draw_card(self.players[self._next_player(True)], 4)
			self.force_colour = True
			self._skip = 1

	def _draw_card(self, player, number=1, silent=False):
		if not silent:
			self.bot.privmsg(self.channel, "{} draws {} card{}.".format(player, number, 's' if number > 1 else ''))

		for i in range(number):
			if len(self.deck) == 0:
				for card in self.discard[:-1]:
					if card[1] == 'W':
						card = 'w'+card[1:]
					self.deck.append(card)
				random.shuffle(self.deck)
				self.bot.privmsg(self.channel, "Discard pile shuffled and added to deck.")
			self.hands[player].append(self.deck.pop())

		if not silent:
			self.bot.notice(player, "Your hand: {}.".format(self._render_hand(player)))

	def _render_hand(self, player, colourblind=-1):
		if colourblind == -1:
			colourblind = (player in self.colourblind_players)
		out = ''
		for card in sorted(self.hands[player]):
			out += self._render_card(card, colourblind)
		return out

	COLOUR_MAP = {
		'r': '00,04',
		'g': '00,03',
		'b': '00,02',
		'y': '01,08',
		'w': '00,01'
	}

	def _render_card(self, card, colourblind=False):
		if colourblind:
			return '[{}]'.format(card)
		else:
			return '\003{}\002[{}]\002\003'.format(self.COLOUR_MAP[card[0]], card[1:])
