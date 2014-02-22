#!/usr/bin/env python3

###############
# Imports
###############
import asynchat
import asyncore
import imp
import json
import kronos
import logging
import os
import re
import socket
import subprocess
import sys
import traceback

from importlib import import_module
from queue import Queue


###############
# Errors
###############
class ConnectionError(Exception):
	pass


class MissingAPIError(Exception):
	pass


logger = logging.getLogger()


###############
# Incoming message parser
###############
class Message:
	"""
	Parses an IRC message into somewhat more usable data.
	"""

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

		if len(args) == 1:
			self.channel = ''
		else:
			self.channel = args.pop(0)

		self.body = trailing

		if not self.body:
			self.body = ' '.join(args)

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
			if self.channel.startswith('#'):
				self.type = Message.CHANNEL
			else:
				self.type = Message.PRIVATE
		else:
			self.type = Message.OTHER

	def ctcp_dequote(self, s):
		return re.sub(r'\\(.)', lambda m: '\001' if m.group(0) == '\\a' else m.group(1), s)


###############
# IRC connection handler
###############
class IRCConnection(asynchat.async_chat):
	"""
	Handles connection to the server, and all the wizz-bang stuff that
	goes along with that.
	"""

	def __init__(self):
		super().__init__()
		self.connected = False

		self.set_terminator(b'\r\n')

		# Flood protection
		self.queue_sched = kronos.ThreadedScheduler()
		self.queue_sched.add_interval_task(self.send_queue, 'FLOOD_SEND_QUEUE', 0, 1, kronos.method.threaded, [], None)
		self.queue_sched.start()
		self.message_queue = Queue()

		self.logger = logger.getChild('IRCConnection')

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

		# Attempt to connect
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		super().connect((self.host, self.port))
		asyncore.loop(timeout=0.2)

	# Called by superclass when the connection is established
	def handle_connect(self):
		self.connected = True

		# Initiate the IRC protocol
		if self.password:
			self.pass_(self.password, now=True)

		self.nick(self.nickname, now=True)
		self.user(self.username, self.realname, now=True)

	# Disconnect from the IRC server
	def disconnect(self, message):
		self.logger.info('disconnect')

		# Bit hard to disconnect if there's not connection in the first place...
		if not self.connected:
			return

		self.quit(message)
		self.handle_close()

	def handle_close(self):
		try:
			self.close()
		except socket.error:
			pass

		self.connected = False

	# Sanitises IRC messages so that they are not misinterpreted by the IRC server.
	def irc_sanitise(self, message):
		return re.sub("[\r\n\0]", "", message)

	# Sends the message to the server. Queues by default.
	def irc_send(self, message, now=False):
		if not self.connected:
			raise ConnectionError('Not connected.')

		# If it's important, or has already been queued
		if now:
			# IRC messages are limited to 512 chars
			if len(message) > 510:
				message = message[:511]

			# Sanitise any unruly characters in output and terminate the message
			message = self.irc_sanitise(message)
			message += '\r\n'

			# Convert the message to a bytes buffer for the socket
			message_bytes = bytes(message, 'UTF-8')
			try:
				self.push(message_bytes)
			except socket.error:
				self.disconnect('Connection reset by peer.')

			self.logger.debug('SENT: ' + message.encode('ascii', 'backslashreplace').decode())

		# Else, queue it
		else:
			self.message_queue.put(message)

	# Flood prevention. Send some stuff from the queue.
	def send_queue(self):
		sent_chars = 0
		# This will still flood if abused.
		while not self.message_queue.empty():
			if sent_chars <= 500:
				message = self.message_queue.get()
				self.irc_send(message, now=True)
				sent_chars += len(message)
			else:
				break

	# Called by superclass with data from the socket
	def collect_incoming_data(self, data):
		self.buffer += data.decode('UTF-8', 'ignore')

	# Called by superclass when terminator (\r\n) found
	def found_terminator(self):
		line = self.buffer
		self.buffer = ''

		self.logger.debug(line.encode('ascii', 'backslashreplace').decode())

		message = Message(line)

		# Handle PINGs ASAP
		if message.command == 'PING':
			self.pong(message.body)
			return

		self.message_recieved(message)

	def message_recieved(self, message):
		raise NotImplementedError()

	###############
	# IRC Protocol commands
	###############

	def invite(self, nick, channel, now=False):
		self.irc_send('INVITE {0} {1}'.format(nick, channel), now)

	def join(self, channel, key='', now=False):
		self.irc_send('JOIN {0}{1}'.format(channel, key and (' ' + key)), now)

	def kick(self, channels, users, comment='', now=False):
		if isinstance(channels, list):
			channels = ','.join(channels)

		if isinstance(users, list):
			users = ','.join(users)

		self.irc_send('KICK {0} {1}{2}'.format(
			channels, users, comment and (' :' + comment)
		), now)

	def mode(self, target, mode, params='', now=False):
		self.irc_send('MODE {0} {1}{2}'.format(
			target, mode, params and (' ' + params)
		), now)

	def names(self, channels, now=False):
		if isinstance(channels, list):
			channels = ','.join(channels)

		self.irc_send('NAMES {0}'.format(channels), now)

	def nick(self, nickname, now=False):
		self.irc_send('NICK ' + nickname, now)

	def notice(self, targets, message, now=False):
		if isinstance(targets, list):
			targets = ','.join(targets)

		self.irc_send('NOTICE {0} :{1}'.format(targets, message), now)

	def pass_(self, password, now=True):
		self.irc_send('PASS ' + password, now)

	def ping(self, target, target2="", now=True):
		self.irc_send('PING {0}{1}'.format(target, target2 and (' ' + target2)), now)

	def pong(self, target, target2="", now=True):
		self.irc_send('PONG {0}{1}'.format(target, target2 and (' ' + target2)), now)

	def privmsg(self, targets, message, now=False):
		if isinstance(targets, list):
			targets = ','.join(targets)

		self.irc_send('PRIVMSG {0} :{1}'.format(targets, message), now)

	def quit(self, message='', now=True):
		message = message or self.nickname
		self.irc_send('QUIT :{0}'.format(message), now)

	def user(self, username, realname, now=True):
		self.irc_send('USER {0} 0 * :{1}'.format(username, realname), now)


###############
# The bot itself
###############
class Ninjabot(IRCConnection):
	VERSION = '2.0.0-dev.py3k'

	def __init__(self, config_path, test_mode=False):
		super().__init__()

		# Work out out absolute directory path
		self.dir = os.path.dirname(os.path.abspath(__file__))

		self.config_path = config_path
		self.load_config()
		self.command_prefix = self.config['bot']['command_prefix']

		self.logger = logger.getChild('Ninjabot')
		if self.config.get('bot', {}).get('debug', False):
		 	logging_level = logging.DEBUG
		else:
	 		logging_level = logging.INFO
		self.logger.setLevel(logging_level)

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
		# The above call will return when the bot is shutting down
		# Kill off the process with the right exit status
		sys.exit(self.exit_status)

	def handle_connect(self):
		super().handle_connect()

		# Connect to channels specified in config
		for channel in self.config['bot']['channels']:
			self.join(channel)

	def handle_close(self):
		self.write_storage()
		return super().handle_close()

	# Called by the connection class with messages from the server
	def message_recieved(self, msg):
		# Catch any errors from the plugins
		try:
			self.on_incoming(msg)
		except:
			self.report_error()

	def on_incoming(self, msg):
		# Ignore the ignored.
		if msg.nick in self.ignored:
			return

		# Check if it's a command
		if msg.body.startswith(self.command_prefix):
			self.handle_command(msg)

		# Not a command? Run it through on_incoming then
		else:
			for func in self.incoming:
				temp_msg = func(msg)

				if temp_msg:
					msg = temp_msg

	def handle_command(self, msg):
		if len(msg.body) == len(self.command_prefix):
			return

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

	def reload(self, msg):
		"Reloads various things."
		if not self.is_admin(msg.nick):
			return

		# For legacy reasons, if nothing provided, assume reloading plugins
		arg = "plugins"
		if msg.args:
			arg = msg.args[0].lower()

		if arg == "plugins":
			self.load_plugins()
		elif arg == "config":
			self.load_config()
		else:
			self.notice(msg.nick, arg+" cannot be reloaded.")
			return

		self.notice(msg.nick, "Reloaded %s successfully." % arg)

	def load_config(self):
		# Need to remove comments, else JSON throws a hissy
		regexp_remove_comments = re.compile(r'/\*.*?\*/', re.DOTALL)

		with open(self.config_path) as fconfig:
			config = fconfig.read()
			self.config = json.loads(regexp_remove_comments.sub('', config))

	###############
	# Plugin handling
	###############

	def load_plugins(self):
		self.clear_plugin_data()

		if 'plugins' not in self.config:
			return

		self.recurse_plugin_config(self.config['plugins'], 'plugins')
		self.initiate_plugins()
		self.setup_storage_write()

	def clear_plugin_data(self):
		# Keep track of plugins so they can be loaded/unloaded
		self.plugins = {}  # TODO

		# Triggers, etc
		self.triggers = {}
		self.incoming = []

		# Register the inbuilt commands
		self.register_inbuilt_triggers()

		# Stop any running timers
		for timer in self.timers:
			self.scheduler.cancel(timer)
		self.timers = []

		# Write storage and reset list to be repopulated by plugins
		self.write_storage()
		self.storage = []

		# Clear out the cache of APIs, they will be reloaded on request
		self.apis = {}

	def register_inbuilt_triggers(self):
		self.triggers['reload'] = self.reload
		self.triggers['kill'] = self.kill
		self.triggers['restart'] = self.restart

	def recurse_plugin_config(self, config, path):
		for key, value in config.items():
			new_path = path + '.' + key
			if value == '*':
				self.load_all_from_path(new_path)
			elif isinstance(value, dict):
				self.recurse_plugin_config(value, new_path)
			elif value:
				self.load(new_path)

	def load_all_from_path(self, path):
		# Get the directory to load from
		load_path = os.path.join(self.dir, *path.split('.'))

		# Loop over files in the directory, attempting to load any .py files
		for file_ in os.listdir(load_path):
			if file_.endswith('.py'):
				# Strip the file extension and load the plugin
				self.load(path + '.' + file_[:-3])

	def load(self, path):
		try:
			# Not pretty, but best I can be assed to do.
			# Anything more requires tomfoolery with sys.modules
			module = imp.reload(import_module(path))
		except:
			self.logger.info("Error while loading {0}. Skipping. Trace:".format(path))
			self.report_error()
			return

		self.load_plugin(path, module)
		self.load_apis(path, module)

	def load_plugin(self, path, module):
		try:
			plugin = module.Plugin()
		except AttributeError:
			# No plugin found, but it might be an API plugin. Fail silently.
			return

		# Register the plugin itself. Don't need the 'plugins.' for every single one.
		name = path.replace('plugins.', '')
		self.plugins[name] = plugin

		# Loop over the plugin's functions and register the ones we want
		for func_name in dir(plugin):
			m_trigger = re.match(r'trigger_(\w+)', func_name)
			m_timer = re.match(r'timer_(\d+)', func_name)

			func = getattr(plugin, func_name)
			if m_trigger:
				self.triggers[m_trigger.group(1).lower()] = func
			elif m_timer:
				t = int(m_timer.group(1))
				timer = self.scheduler.add_interval_task(func, path+func_name, 0, t, kronos.method.threaded, [], None)
				self.timers.append(timer)
			elif func_name == 'on_incoming':
				self.incoming.append(func)

	def load_apis(self, path, module):
		try:
			apis = module.APIS
		except AttributeError:
			# No API found (not really surprising), fail silently.
			return

		# We have a dict of APIs, keep record of them.
		for name, api in apis.items():
			self.apis[name] = api

	def initiate_plugins(self):
		for name, plugin in self.plugins.items():
			# Get the plugin's config, if it exists
			config = {}
			if name in self.config:
				config = self.config[name]

			plugin.load(self, config)

	###############
	# API stuff
	###############

	def request_api(self, name, required=True):
		if name in self.apis:
			return self.apis[name]
		else:
			if required:
				raise MissingAPIError("The required API '{0}' was not found.".format(name))
			else:
				return None

	###############
	# Storage stuff
	###############

	def setup_storage_write(self):
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
		self.logger.info('Writing storage to disk')
		for s in self.storage:
			s.write()

	###############
	# Things that hurt the bot (you should feel bad)
	###############

	def kill(self, msg):
		if not self.is_admin(msg.nick):
			return

		message = self.config['bot']['quit_message']

		if len(msg.args):
			message = ' '.join(msg.args)

		self.disconnect(message)

	def restart(self, msg):
		if not self.is_admin(msg.nick):
			return

		self.exit_status = 0
		self.kill(msg)

	###############
	# Miscellaneous functions
	###############

	def report_error(self):
		error = traceback.format_exc()
		logging.error(error)
		self.errors.append(error)

		if self.config['bot']['notify_errors'] and self.connected:
			self.privmsg(','.join(self.config['bot']['channels']), "An error occurred. Please ask an admin to check error log {0}.".format(len(self.errors)-1))

	def is_admin(self, nickname, silent=False):
		if nickname in self.admins:
			return True

		if self.config['bot']['notify_insufficient_privs'] and not silent:
			self.notice(nickname, "You have insufficient privileges to perform that action.")

		return False

	def is_ignored(self, nickname):
		if nickname in self.ignored:
			return True
		return False

	def schedule(self, time, function, *args, **kwargs):
		task = self.scheduler.add_single_task(function, str(hash(function)), time, kronos.method.threaded, args, kwargs)
		self.timers.append(task)
		return task

	def cancel_schedule(self, task):
		try:
			self.timers.remove(task)
		except ValueError:
			pass

		try:
			self.scheduler.cancel(task)
		except ValueError:
			pass


# Entry point
def ninjabot_main():
	args = sys.argv[1:]

	# If it's not wrapped, wrap it
	if 'wrapped' not in args:
		ninjabot_wrap()

	logger.setLevel(logging.INFO)
	logger.addHandler(logging.StreamHandler())

	# Else, start up the bot
	logger.info('ninjabot starting up')

	if '-c' in args:
		config_filename = args[args.index('-c') + 1]
	else:
		config_filename = os.path.join(os.path.expanduser('~'), '.ninjabot_config')

	bot = Ninjabot(config_filename)
	bot.start()


# Wrap another process of the bot to allow restarts
def ninjabot_wrap():
	# Launch the wrapper
	logger.info('ninjabot wrapper up and running!')
	while not False:
		logger.info('Starting instance...\n')
		process_args = [sys.executable] + sys.argv + ['wrapped']
		process = subprocess.Popen(process_args, shell=False)
		try:
			status = process.wait()
		except KeyboardInterrupt:
			process.kill()
			status = 1

		if status != 0:
			logger.info('\nGoodbye!')
			sys.exit()
		else:
			logger.info('\nRestarting ninjabot')

if __name__ == '__main__':
	ninjabot_main()
