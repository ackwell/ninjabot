import json
import kronos
import os
import re
import socket
import subprocess
import sys
import time
import traceback

from importlib import import_module
from Queue import Queue

# Errors
class ConnectionError(Exception): pass

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
			# Encode the message.
			message = message.encode('utf-8', 'ignore')
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

				# Encode, then chuck through the Message whatsit
				line = unicode(line, 'utf-8', 'ignore')
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
	def __init__(self, config_path):
		IRCConnection.__init__(self)

		self.config_path = config_path
		self.load_config()

		# List of errors n' stuff
		self.errors = []

		# Bot admins. Authentication is handled externally (plugin)
		self.admins = []

		# Start up the shcduler for timer plugins
		self.scheduler = kronos.ThreadedScheduler()
		self.scheduler.start()
		self.timers = []

		# Exit without restarting by default
		self.exit_status = 1

		self.load_plugins()

	def start(self):
		self.connect(**self.config['server'])

		# Connect to channels specified in config
		for channel in self.config['bot']['channels']:
			self.join(channel)

		self.command_prefix = self.config['bot']['command_prefix']

		# Generator that spews messages from the server
		for msg in self.process_loop():
			# Catch any errors from the plugins
			try:
				self.on_incoming(msg)
			except:
				self.report_error()

		# Loop has exited - exit the process
		sys.exit(self.exit_status)

	def on_incoming(self, msg):
		# Check if it's a command
		if msg.body.startswith(self.command_prefix):
			if len(msg.body) == len(self.command_prefix): return
			# Strip the prefix
			msg.body = msg.body[len(self.command_prefix):]

			# Get the command and stuff
			msg_split = msg.body.split(None, 1)
			command, argument = msg_split[0].lower(), msg_split[1] if len(msg_split)>1 else ''
			msg.argument = argument

			# Try to call the trigger
			if command in self.triggers:
				self.triggers[command](msg)
			elif self.config['bot']['notify_cnf']:
				self.notice(msg.nick, command+' is not a valid command.')

		# Not a command? Run it through on_incoming then
		else:
			for func in self.incoming:
				temp_msg = func(msg)
				if temp_msg: msg = temp_msg

	def reload(self, msg):
		"Reloads various things."
		if not self.isadmin(msg.nick): return

		arg = msg.argument.lower()
		# For legacy reasons, if nothing provided, assume reloading plugins
		if not len(arg): arg = 'plugins'
		if arg == "plugins":
			self.load_plugins()
		elif arg == "config":
			self.load_config()
		else:
			self.notice(msg.nick, arg+" cannot be reloaded.")

		self.notice(msg.nick, "Reloaded sucessfully.")

	def load_config(self):
		# Need to remove comments, else JSON throws a hissy
		regexp_remove_comments = re.compile(r'/\*.*?\*/', re.DOTALL)
		config = open(self.config_path, 'rU').read()
		self.config = json.loads(regexp_remove_comments.sub('', config))

	def load_plugins(self):
		self.triggers = {}
		self.incoming = []

		# Register base functions
		self.triggers['reload'] = self.reload
		self.triggers['kill'] = self.kill
		self.triggers['restart'] = self.restart

		# Stop any running timers
		for timer in self.timers:
			self.scheduler.cancel(timer)
		self.timers = []

		# Get a list of plugins
		l = []
		for f in os.listdir('./Plugins'):
			if f.endswith('.py'):
				l.append(f[:-3])

		# Try to import them
		for mod in l:
			# Skip over disabled plugins
			if 'plugins' in self.config and mod in self.config['plugins'] and not self.config['plugins'][mod]:
				continue

			# Get the plugin's config, if it exists
			config = {}
			if mod in self.config:
				config = self.config[mod]

			try:
				# Not pretty, but best I can be assed to do.
				# Anything more requires tomfoolery with sys.modules
				plugin = reload(import_module('Plugins.' + mod)).Plugin(self, config)
			# Probably the __init__ file...
			except AttributeError:
				continue
			except:
				self.report_error()
				continue

			# Register plugin functions
			for func_name in dir(plugin):
				m_trigger = re.match(r'trigger_(.+)', func_name)
				m_timer = re.match(r'timer_([0-9]+)', func_name)

				func = getattr(plugin, func_name)
				if m_trigger:
					self.triggers[m_trigger.group(1).lower()] = func
				elif m_timer:
					t = int(m_timer.group(1))
					timer = self.scheduler.add_interval_task(func, mod+func_name, 0, t, kronos.method.threaded, [], None)
					self.timers.append(timer)
				elif func_name == 'on_incoming':
					self.incoming.append(func)

	def kill(self, msg):
		if not self.isadmin(msg.nick): return
		message = self.config['bot']['quit_message']
		if len(msg.argument):
			message = msg.argument
		self.disconnect(message)

	def restart(self, msg):
		if not self.isadmin(msg.nick): return
		self.exit_status = 0
		self.kill(msg)

	def report_error(self):
		error = traceback.format_exc()
		print error
		self.errors.append(error)
		if self.config['bot']['notify_errors']:
			self.privmsg(','.join(self.config['bot']['channels']), "An error occured. Please ask an admin to check error log %i."%(len(self.errors)-1))

	def isadmin(self, nickname, silent=False):
		if nickname in self.admins:
			return True
		if self.config['bot']['notify_insufficient_privs'] and not silent:
			self.notice(nickname, "You have insufficient privilages to perform that action.")
		return False

if __name__ == '__main__':
	# Grab the command line args
	args = sys.argv[1:]

	if 'wrapped' not in args:
		# Launch the wrapper
		print 'ninjabot wrapper up and running!'
		while not False:
			print 'Starting instance...\n'
			process_args = [sys.executable] + sys.argv + ['wrapped']
			process = subprocess.Popen(process_args, shell=False)
			try:
				status = process.wait()
			except KeyboardInterrupt:
				process.kill()
				status = 1

			if status != 0:
				print '\nGoodbye!'
				quit()
			else:
				print '\nRestarting ninjabot'

	print 'ninjabot starting up'

	# Check if a config file path has been specified
	if '-c' in args:
		config_filename = args[args.index('-c') + 1]
	else:
		config_filename = os.path.join(os.path.expanduser('~'), '.ninjabot_config')

	# Start up the bot
	bot = ninjabot(config_filename)
	bot.start()
