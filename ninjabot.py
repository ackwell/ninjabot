#!/usr/bin/env python3

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
from queue import Queue

class ConnectionError(Exception): pass

class Message:
	OTHER   = 0
	CHANNEL = 1
	PRIVATE = 2

	NUMERIC = {
		'NAMREPLY': '353',
		'ENDOFNAMES': '366'
	}

	# Parse the message, set variables
	def __init__(self, message):
		prefix = ''
		trailing = ''

		if message[0] == ':':
			prefix, message = message[1:].split(' ', 1)

		# Get the arguments. If there is a string arg, don't split it.
		if message.find(' :') != -1:
			message, trailing = message.split(' :', 1)
			args = message.split()
			args.append(trailing)
		else:
			args = message.split()

		# Split the args into command/channel/body
		self.command = args.pop(0)
		if len(args) == 1: self.channel = ''
		else: self.channel = args.pop(0)
		self.body = trailing if trailing else ' '.join(args)

		# Save any additional arguments
		if len(args) >= 1:
			self.data = args[:-1]

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

		# Extract any CTCP stuff if it's in there
		m = re.search(r'\001(.+)\001', self.body)
		if m:
			self.ctcp = self.ctcp_dequote(m.group(1))
			self.body = self.body.replace(m.group(0), '')
		else:
			self.ctcp = ''

		# Set what type of message it is
		if self.command == 'PRIVMSG':
			if self.channel.startswith('#'): self.type = Message.CHANNEL
			else: self.type = Message.PRIVATE
		else: self.type = Message.OTHER

	def ctcp_dequote(self, s):
		return re.sub(r'\\(.)', lambda m:'\001' if m.group(0)=='\\a' else m.group(1), s)

# Handles connection to the IRC server
class IRCConnection(object):
	def __init__(self):
		self.connected = False
		self.socket = None

		# Flood protection
		self.message_queue = Queue()
		self.sent_chars = 0
		self.sent_time_last = time.time()
		self.sent_time = 0

	# Connect to the IRC server
	def connect(self, host, port, nickname, username='', realname='', password=''):
		self.host = host
		self.port = port

		self.nickname = nickname
		self.username = username or self.nickname
		self.realname = realname or self.username
		self.password = password

		self.buffer = ''
		self.connected = False

		# Get a socket, toss an error if it can't connect
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.socket.connect((self.host, self.port))
		except socket.error:
			self.socket.close()
			self.socket = None
			raise ConnectionError('Error connecting to socket.')
		self.socket.settimeout(0.2)

		self.connected = True

		# Initiate the IRC protocol
		if self.password: self.pass_(self.password, now=True)
		self.nick(self.nickname, now=True)
		self.user(self.username, self.realname, now=True)

	# Disconnect from the IRC server
	def disconnect(self, message):
		# Bit hard to disconnect if there's not connection in the first place...
		if not self.connected: return

		self.quit(message)

		# Ensure that things are kept persistant
		self.write_storage()

		# Close the socket
		try: self.socket.close()
		except socket.error: pass
		self.socket = None

		self.connected = False

	# Sends the message to the server. Queues by default.
	def send(self, message, now=False):
		if self.socket is None: raise ConnectionError('Not connected.')

		# If it's important, or has already been queued
		if now:
			# IRC messages are limited to 512 chars
			if len(message) > 510:
				message = message[:511]
			message += '\r\n'
			# Convert the message to a bytes buffer for the socket
			message_bytes = bytes(message, 'UTF-8')
			try: self.socket.sendall(message_bytes)
			except socket.error: self.disconnect('Connection reset by peer.')

			# For debug
			if 'debug' in self.config['bot'] and self.config['bot']['debug']:
				print('SENT: ' + message)

		# Else, queue it
		else:
			self.message_queue.put(message)

	# Flood prevention. Send some stuff from the queue.
	def send_queue(self):
		time_now = time.time()
		self.sent_time += time_now - self.sent_time_last
		self.sent_time_last = time_now
		if self.sent_time > 1.0:
			self.sent_time = 0
			self.sent_chars = 0

		# This will still flood if abused.
		while not self.message_queue.empty():
			if self.sent_chars <= 500:
				message = self.message_queue.get()
				self.send(message, now=True)
				self.sent_chars += len(message)
			else:
				break

	# Recieve data from the server
	def recieve(self):
		new_data = b''
		try:
			new_data = self.socket.recv(2**14)
			if not new_data: self.disconnect('Connection reset by peer.')
		except socket.timeout: pass
		except socket.error: self.disconnect('Connection reset by peer.')

		# Some IRCd don't use \r in the delimiter
		lines = re.split(r'\r?\n', self.buffer + new_data.decode('UTF-8'))
		self.buffer = lines.pop()
		return lines

	def process_loop(self):
		while self.connected:
			lines = self.recieve()

			for line in lines:
				# Debug
				if 'debug' in self.config['bot'] and self.config['bot']['debug']:
					print(line)

				message = Message(line)

				# Handle PINGs ASAP
				if message.command == 'PING':
					self.pong(message.body)
					continue

				yield message

			self.send_queue()

	# IRC Commands

	def invite(self, nick, channel, now=False):
		self.send('INVITE {0} {1}'.format(nick, channel), now)

	def join(self, channel, key='', now=False):
		self.send('JOIN {0}{1}'.format(channel, key and (' ' + key)), now)

	def kick(self, channels, users, comment='', now=False):
		if isinstance(channels, list): channels = ','.join(channels)
		if isinstance(users, list): users = ','.join(users)
		self.send('KICK {0} {1}{2}'.format(
			channels, users, comment and (' :' + comment)
		), now)

	def mode(self, target, mode, params='', now=False):
		self.send('MODE {0} {1}{2}'.format(target, mode, params and (' ' + params)))

	def names(self, channels, now=False):
		if isinstance(channels, list): channels = ','.join(channels)
		self.send('NAMES {0}'.format(channels), now)

	def nick(self, nickname, now=False):
		self.send('NICK ' + nickname, now)

	def notice(self, targets, message, now=False):
		if isinstance(targets, list): targets = ','.join(targets)
		self.send('NOTICE {0} :{1}'.format(targets, message), now)

	def pass_(self, password, now=True):
		self.send('PASS ' + password, now)

	def ping(self, target, target2="", now=True):
		self.send('PING {0}{1}'.format(target, target2 and (' ' + target2)), now)

	def pong(self, target, target2="", now=True):
		self.send('PONG {0}{1}'.format(target, target2 and (' ' + target2)), now)

	def privmsg(self, targets, message, now=False):
		if isinstance(targets, list): targets = ','.join(targets)
		self.send('PRIVMSG {0} :{1}'.format(targets, message), now)

	def quit(self, message, now=True):
		self.send('QUIT' + (message and (' :' + message)), now)

	def user(self, username, realname, now=True):
		self.send('USER {0} 0 * :{1}'.format(username, realname), now)

class Ninjabot(IRCConnection):
	def __init__(self, config_path):
		super().__init__()

		self.config_path = config_path
		self.load_config()

		# List of errors n' stuff
		self.errors = []

		# Bot admins. Authentication is handled externally (plugin)
		self.admins = []

		# Ignored users. Again, handled by a plugin.
		self.ignored = []

		# List of storages that should be written to disk on a timer
		self.storage = []

		# Start up the scheduler for timer plugins
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
			args = msg.body.split()
			command = args.pop(0)
			msg.args = args

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
		if not self.is_admin(msg.nick): return

		# For legacy reasons, if nothing provided, assume reloading plugins
		arg = msg.args[0].lower() if len(msg.args) else 'plugins'
		if arg == "plugins":
			self.load_plugins()
		elif arg == "config":
			self.load_config()
		else:
			self.notice(msg.nick, arg+" cannot be reloaded.")
			return

		self.notice(msg.nick, "Reloaded %s sucessfully." % arg)

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

		# TEMP
		return

		# Stop any running timers
		for timer in self.timers:
			self.scheduler.cancel(timer)
		self.timers = []

		# Write storage and reset list to be repopulated by plugins
		self.write_storage()
		self.storage = []

		# Get a list of plugins
		l = []
		for f in os.listdir('./Plugins'):
			if f.endswith('.py'):
				l.append(f[:-3])

		# Get the default state for plugins
		default_should_load = False
		if 'plugin_default_status' in self.config['bot']:
			default_should_load = self.config['bot']['plugin_default_status']

		# Try to import them
		for mod in l:
			# Only load mods that have been enabled
			should_load = default_should_load
			if 'plugins' in self.config and mod in self.config['plugins']:
				should_load = self.config['plugins'][mod]
			if not should_load:
				continue

			# Get the plugin's config, if it exists
			config = None
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

		# Add timer to periodically write to disk
		interval = self.config.get('storage', {}).get('writeinterval', 0)
		alwayswrite = self.config.get('storage', {}).get('alwayswrite', False)
		if not alwayswrite and interval == 0:
			interval = 300
		if interval != 0:
			self.timers.append(self.scheduler.add_interval_task(self.write_storage, 'STORAGE TASK', 0, interval, kronos.method.threaded, [], None))

	def register_storage(self, store):
		self.storage.append(store)

	def write_storage(self):
		print('Writing storage to disk')
		for s in self.storage:
			s.write()

	def kill(self, msg):
		if not self.is_admin(msg.nick): return
		message = self.config['bot']['quit_message']
		if len(msg.args):
			message = ' '.join(msg.args)
		self.disconnect(message)

	def restart(self, msg):
		if not self.is_admin(msg.nick): return
		self.exit_status = 0
		self.kill(msg)

	def report_error(self):
		error = traceback.format_exc()
		print(error)
		self.errors.append(error)
		if self.config['bot']['notify_errors']:
			self.privmsg(','.join(self.config['bot']['channels']), "An error occured. Please ask an admin to check error log {0}.".format(len(self.errors)-1))

	def is_admin(self, nickname, silent=False):
		if nickname in self.admins:
			return True
		if self.config['bot']['notify_insufficient_privs'] and not silent:
			self.notice(nickname, "You have insufficient privilages to perform that action.")
		return False

	def is_ignored(self, nickname):
		if nickname in self.ignored:
			return True
		return False

	def schedule(self, time, function, *args, **kwargs):
		self.scheduler.add_single_task(function, str(hash(function)), time, kronos.method.threaded, args, kwargs)

if __name__ == '__main__':
	args = sys.argv[1:]

	if 'wrapped' not in args:
		# Launch the wrapper
		print('ninjabot wrapper up and running!')
		while not False:
			print('Starting instance...\n')
			process_args = [sys.executable] + sys.argv + ['wrapped']
			process = subprocess.Popen(process_args, shell=False)
			try:
				status = process.wait()
			except KeyboardInterrupt:
				process.kill()
				status = 1

			if status != 0:
				print('\nGoodbye!')
				quit()
			else:
				print('\nRestarting ninjabot')

	print('ninjabot starting up')

	if '-c' in args:
		config_filename = args[args.index('-c') + 1]
	else:
		config_filename = os.path.join(os.path.expanduser('~'), '.ninjabot_config')

	bot = Ninjabot(config_filename)
	bot.start()
