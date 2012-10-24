import json
import kronos
import os
import re
import socket
import sys
import time

from importlib import import_module
from Queue import Queue

# Errors
class ConnectionError(Exception): pass

# NOTE: PING TARGET IN SELF.BODY

# class used to hold message data in a slightly more useful manner
class Message:
	OTHER   = 0
	CHANNEL = 1
	PRIVATE = 2

	def __init__(self, message):
		prefix = ''
		trailing = ''

		if message[0] == ':':
			prefix, message = message[1:].split(' ', 1)

		# Get the arguments. If there's a string argument, don't split it up.
		if message.find(' :') != -1:
			message, trailing = message.split(' :', 1)
			args = message.split()
			args.append(trailing)
		else:
			args = message.split()

		# Split args into command/channel/body
		self.command = args.pop(0)
		if len(args) == 1: self.channel = ""
		else: self.channel = args.pop(0)
		self.body = trailing if trailing else ' '.join(args)

		# Split the prefix into something a bit more useful
		if '!' in prefix:
			self.nick, userhost = prefix.split('!', 2)
			if '@' in userhost:
				self.user, self.host = userhost.split('@', 2)
			else:
				self.user = userhost
				self.host = ''
		else:
			self.nick = prefix
			self.user = self.host = ''

		# Extract any CTCP stuff if it's there
		m = re.search(r'\001(.+)\001', self.body)
		if m:
			self.ctcp = self.ctcp_dequote(m.group(1))
			self.body = self.body.replace(m.group(0), '')
		else:
			self.ctcp = ''

		# Check what type of message it is
		if self.command == 'PRIVMSG':
			if self.channel.startswith('#'): self.type = Message.CHANNEL
			else: self.type = Message.PRIVATE
		else: self.type = Message.OTHER

	def ctcp_dequote(self, s):
		return re.sub(r'\\(.)', lambda m:'\001' if m.group(0)=='\\a' else m.group(1), s)


# Creates and handles connection to IRC server
class IRCConnection:
	def __init__ (self):
		self.connected = False
		self.socket = None

		# Flood protection
		self.message_queue = Queue()
		self.sent_chars = 0
		self.sent_time_last = time.time()
		self.sent_time = 0


	# Connect to the IRC server
	def connect(self, host, port, nickname, username="", realname="", password=""):
		self.host = host
		self.port = port

		self.nickname = nickname
		self.username = username or nickname
		self.realname = realname or username
		self.password = password

		self.buffer = ''
		self.connected = False

		# Get a socket
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.socket.connect((self.host, self.port))
		except socket.error:
			self.socket.close()
			self.socket = None
			raise ConnectionError, "Error connecting to socket."
		self.socket.settimeout(0.2)

		self.connected = True

		# Connect to the server
		if self.password: self.pass_(self.password)
		self.nick(self.nickname)
		self.user(self.username, self.realname)

	# Disconnect from the IRC server
	def disconnect(self, message):
		# Can't disconect if we don't have a connection...
		if not self.connected: return

		self.quit(message)

		# Close the socket
		try: self.socket.close()
		except socket.error: pass
		self.socket = None

		self.connected = False

	# Send a message to the server. Delimiter is added automatically
	def send(self, message, now=False):
		if self.socket is None: raise ConnectionError, "Not connected."

		# If it's imporant (or has already been queued)
		if now:
			# Max message length for IRC is 512 chr.
			if len(message) > 510:
				message = message[:511]
			message += "\r\n"
			try:
				self.socket.sendall(message)
			except socket.error: self.disconnect("Connection reset by peer.")

			# DEBUG
			print "SENT: " + message

		# Else, queue it
		else:
			# Encode the message. Uncomment if shit goes down.
			#message = message.encode('utf-8', 'ignore')
			self.message_queue.put(message)

	# Send some stuff from the queue. Used for flood prevention.
	def send_queue(self):
		self.sent_time += time.time() - self.sent_time_last
		self.sent_time_last = time.time()
		if self.sent_time >= 1.0:
			self.sent_time = 0
			self.sent_chars = 0

		# This *WILL STILL FLOOD* if abused.
		# Should keep it to a minimum, however.
		while not self.message_queue.empty():
			if self.sent_chars <= 500:
				message = self.message_queue.get()
				self.send(message, now=True)
				self.sent_chars += len(message)
			else:
				break

	# Recieve data from the server.
	def receive(self):
		new_data = ''
		try:
			new_data = self.socket.recv(2**14)
			if not new_data: self.disconnect("Connection reset by peer.")
		except socket.timeout: pass
		except socket.error: self.disconnect("Connection reset by peer.")

		# 'parrently some IRCd don't use the \r in their delimiter
		lines = re.split(r'\r?\n', self.buffer + new_data)
		self.buffer = lines.pop()

		return lines

	def process_loop(self):
		while self.connected:
			lines = self.receive()

			for line in lines:
				# DEBUG
				print line

				message = Message(line)

				# Handle PINGs ASAP
				if message.command == 'PING':
					self.pong(message.body)
					continue

				yield message

			self.send_queue()

	# IRC Commands

	def join(self, channel, key=""):
		self.send("JOIN %s%s" % (channel, key and (" " + key)))

	def nick(self, nickname):
		self.send("NICK " + nickname)

	def pass_(self, password):
		self.send("PASS " + password)

	def ping(self, target, target2=""):
		self.send("PING %s%s" % (target, target2 and (" " + target2)), now=True)

	def pong(self, target, target2=""):
		self.send("PONG %s%s" % (target, target2 and (" " + target2)), now=True)

	def privmsg(self, targets, message):
		if type(targets) is list: targets = ','.join(targets)
		self.send("PRIVMSG %s :%s" % (targets, message))

	def notice(self, targets, message):
		if type(targets) is list: targets = ','.join(targets)
		self.send("NOTICE %s :%s" % (targets, message))

	def quit(self, message):
		self.send("QUIT" + (message and (" :" + message)), now=True)

	def user(self, username, realname):
		self.send("USER %s 0 * :%s" % (username, realname))




class ninjabot(IRCConnection):
	def __init__(self, config):
		IRCConnection.__init__(self)

		self.config = config

		# Start up the shcduler for timer plugins
		#self.scheduler = kronos.ThreadedScheduler()
		#self.scheduler.start()
		#self.timers = []

		self.load_plugins()

	def start(self):
		self.connect(**self.config['server'])

		# Connect to channels specified in config
		for channel in self.config['bot']['channels']:
			self.join(channel)

		command_prefix = self.config['bot']['command_prefix']

		# Generator that spews messages from the server
		for msg in self.process_loop():
			# Check if it's a command
			if msg.body.startswith(command_prefix):
				if len(msg.body) == len(command_prefix): continue
				# Strip the prefix
				msg.body = msg.body[len(command_prefix):]

				# Get the command and stuff
				msg_split = msg.body.split(None, 1)
				command, argument = msg_split[0], msg_split[1] if len(msg_split)>1 else ''
				msg.argument = argument

				# Try and call the trigger
				if command in self.triggers:
					self.triggers[command](msg)
				elif self.config['bot']['notify_cnf']:
					self.notice(msg.nick, command+' is not a valid command.')

			# Not a command? Run it through on_incoming then
			else:
				for func in self.incoming:
					temp_msg = func(msg)
					if temp_msg: msg = temp_msg


	def load_plugins(self, msg=None):
		"Reloads plugins"

		self.triggers = {}
		self.incoming = []

		# Register base functions
		self.triggers['reload'] = self.load_plugins

		# Stop any running timers
		#for timer in self.timers:
		#	self.scheduler.cancel(timer)
		#self.timers = []

		# Get a list of plugins
		l = []
		for f in os.listdir('./Plugins'):
			if f.endswith('.py'):
				l.append(f[:-3])

		# Try to import them
		for mod in l:
			modname = 'Plugins.' + mod

			# Need to check if plugin is enabled in the config here.
			try:
				# Not pretty, but best I can be assed to do.
				# Anything more requires tomfoolery with sys.modules
				plugin = reload(import_module(modname)).Plugin(self)
			# Probably the __init__ file...
			except AttributeError:
				continue
			except Exception as e:
				# Report the error
				continue

			# Register plugin functions
			for func_name in dir(plugin):
				m_trigger = re.match(r'trigger_(.+)', func_name)
				#m_timer = re.match(r'timer_([0-9]+)', func_name)

				func = getattr(plugin, func_name)
				if m_trigger:
					self.triggers[m_trigger.group(1)] = func
				#add timer
				elif func_name == 'on_incoming':
					self.incoming.append(func)

		# If reload was issued from channel, message the caller to notify completion
		if msg:
			self.notice(msg.nick, "Reloaded sucessfully.")








if __name__ == '__main__':
	# Grab the command line args
	args = sys.argv[1:]

	# Check if a config file path has been specified
	if '-c' in args:
		config_filename = args[args.index('-c') + 1]
	else:
		config_filename = os.path.join(os.path.expanduser('~'), '.ninjabot_config')

	# Need to remove comments, else JSON throws a hissy
	regexp_remove_comments = re.compile(r'/\*.*?\*/', re.DOTALL)
	config = open(config_filename, 'rU').read()
	config = json.loads(regexp_remove_comments.sub('', config))

	# Start up the bot
	bot = ninjabot(config)
	bot.start()






































# Whitespace because ST2 on OSX seems not to have the extra buffer space
# Please excuse