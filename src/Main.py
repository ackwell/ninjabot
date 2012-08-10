import re
import socket
import sys
import threading
import traceback
import os
import json
import kronos
import unicodedata

from Interface import *
from importlib import import_module

# constants are here temporarily
# maybe move to a config file in the future

class Message:
	OTHER = 0
	CHANNEL = 1
	PRIVATE = 2

	PRIVMSG = 'PRIVMSG'
	NOTICE = 'NOTICE'
	JOIN = 'JOIN'
	PART = 'PART'
	QUIT = 'QUIT'
	MODE = 'MODE'
	NICK = 'NICK'
	
	def __init__(self, message=None):
		if message:
			prefix = ''
			trailing = []
			
			if not message:
				raise Exception("Empty line.")
			
			if message[0] == ':':
				prefix, message = message[1:].split(' ', 1)
				
			if message.find(' :') != -1:
				message, trailing = message.split(' :', 1)
				args = message.split()
				args.append(trailing)
			else:
				args = message.split()
			
			#get command, channel, body
			self.command = args.pop(0)
			if len(args) == 1:
				self.channel = ""
				self.body = " ".join(args)
			else:
				self.channel = args.pop(0)
				self.body = " ".join(args)

			#split the prefix
			if '!' in prefix:
				self.nick, userhost = prefix.split('!', 2)
				if '@' in userhost:
					self.user, self.host = userhost.split('@', 2)
				else:
					self.user = userhost
					self.host = ''
			else:
				self.nick = prefix
				self.user = ''
				self.host = ''

			#get any CTCP stuff
			m = re.search(r'\001(.+)\001', self.body)
			if m:
				self.ctcp = self.ctcp_dequote(m.group(1))
				self.body = self.body.replace(m.group(0), '')
			else:
				self.ctcp = ''

			#set message type
			if self.command == 'PRIVMSG' and self.channel.startswith('#'):
				self.type = Message.CHANNEL
			elif self.command == 'PRIVMSG':
				self.type = Message.PRIVATE
			else:
				self.type = Message.OTHER

		else:
			# no message provided? that's fine!
			# initialise all the vars!
			self.type = Message.OTHER
			self.command = ''
			self.channel = ''
			self.nick = ''
			self.host = ''
			self.body = ''
			self.ctcp = ''

	def ctcp_dequote(self, s):
		return re.sub(r'\\(.)', lambda m:'\001' if m.group(0)=='\\a' else m.group(1), s)
			
	def __str__(self):
		try:
			return '%s %s :%s%s\r\n' % (self.command, self.channel, self.body, '\001%s\001'%self.ctcp if self.ctcp else '',)
		except NameError:
			raise Exception('One or more required properties were not set on the Message object')

class SocketListener(threading.Thread):
	#List used to store logs when GUI is being used
	#GUI checks this list every second
	LOG = []
	
	def __init__(self, config):
		self.config = config
		
		# Initialise the socket and connect
		# Also set the socket to non-blocking, so if there is no data to
		# read, the .recv() operation will not hang
		self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self._sock.connect((self.config['server']['host'], self.config['server']['port']))
		self._sock.settimeout(0.1)

		# Initialise some vars
		self._stop = False
		self._stopped = False
		self._write_buffer = []
		
		# Initialise the superclass
		threading.Thread.__init__(self)
	
	def run(self):
		# Send our love to the server
		self._sock.send('NICK %s\r\n' % self.config['config']['nick'])
		self._sock.send('USER %s 0 * :%s\r\n' % (self.config['config']['nick'], self.config['config']['realname']))
		self._sock.send('JOIN :%s\r\n' % self.config['server']['channel'])
		
		# Initialise the read buffer
		read_buffer = ''
		while not self._stop:
			# Write bytes as needed
			while len(self._write_buffer) > 0:
				self._sock.send(self._write_buffer.pop(0))
			
			# Read bytes as needed
			try:
				read_buffer += self._sock.recv(1)
			except socket.error:
				continue
			
			# Check whether we've formed a complete message
			if read_buffer.endswith('\r\n'):
				msg = read_buffer[:-2]
				read_buffer = ''
				
				# Firstly, check for ping
				m = re.match(r'^PING :(.+)$', msg)
				if m:
					self.send('PONG :%s\r\n' % m.group(1))
				else:
					# Create message object
					try:
						msg_obj = Message(msg)
						self.controller.incoming_message(msg_obj)
					except Exception as e:#Exception as e:
						#print e, msg
						traceback.print_exc()
						print
					#msg_obj = Message(msg)
					#self.controller.incoming_message(msg_obj)

		
		# Once we are told to stop, send the quit message, close the socket,
		# and end the thread
		self._sock.send('QUIT :%s\r\n' % self.config['config']['quit-message'])
		self._sock.close()
		self._stopped = True
	
	def stop(self):
		# Set the stop variable to true and wait for the thread to finish
		# doing whatever it is it's doing
		self._stop = True
		while not self._stopped: pass
	
	def send(self, data):
		# Add a line to the write buffer
		self._write_buffer += [data]
	
	def send_message(self, msg):
		# Add the string representation of the Message object to the
		# write buffer
		self.send(msg.__str__().encode('utf-8','ignore'))

class Controller:
	def __init__(self, sl, gui, config):
		# Give ourselves a reference to the SocketListener & GUI
		self.sl = sl
		self.gui = gui
		self.config = config

		# And give our own reference to them
		self.sl.controller = self
		self.gui.controller = self

		# List of channels we are on
		self.channels = [self.config['server']['channel']]

		#initiate the plugin system
		self.plugins = PluginHandler(self)

		#initiate the buffer that the GUI will poll for updates
		self.buffer = [];



		self._should_die = False
	
	def begin(self):
		# Start the SocketListener
		self.sl.start()
		#self.gui.mainloop()
		self.gui.startloop()

		self.sl.stop()

	def incoming_message(self, msg):
		# Received message object from the sl
		# Parse it and display it in the gui
		msg = self.plugins.on_incoming(msg)

		self.buffer.append(msg) #add the message to the buffer
	
	def outgoing_message(self, msg):
		# Received message object
		# Send it through the sl and to the gui for displaying

		# run messages through the plugin sys
		msg = self.plugins.on_outgoing(msg)

		self.sl.send_message(msg)
		self.buffer.append(msg) #add the message to the buffer

	def is_admin(self, nick):
		return True if nick in self.config['config']['admins'].split() else False

	def notice(self, target, message, ctcp=''):
		msg = Message()
		msg.command = Message.NOTICE
		msg.channel = target
		msg.body = message
		msg.ctcp = ctcp
		self.outgoing_message(msg)

	def privmsg(self, target, message, ctcp=''):
		msg = Message()
		msg.command = Message.PRIVMSG
		msg.channel = target
		msg.body = message
		msg.ctcp = ctcp
		self.outgoing_message(msg)

	def join(self, channel):
		msg = Message()
		msg.command = Message.JOIN
		msg.body = channel
		self.outgoing_message(msg)

	def part(self, channel):
		msg = Message()
		msg.command = Message.PART
		msg.body = channel
		self.outgoing_message(msg)
	
	def die(self):
		self.sl.stop()
		self.plugins.scheduler.stop()
		quit()



class PluginHandler:
	def __init__(self, controller):
		self.controller = controller
		self.prefix = self.controller.config['config']['trigger-prefix']

		self.scheduler = kronos.ThreadedScheduler()
		self.scheduler.start()
		self.timers = []

		self.register()

	def register(self, msg=None):
		"Reloads all plugins. Admin only."

		if msg and not self.controller.is_admin(msg.nick):
			self.controller.notice(msg.nick, "You are not permitted to use this command.")
			return

		self.triggers = {}
		self.incoming = []
		self.outgoing = []

		self.triggers['reload'] = self.register

		# Cancel the scheduler jobs
		for timer in self.timers:
			self.scheduler.cancel(timer)
		self.timers = []

		l = []
		#get a list of plugins
		for f in os.listdir('./Plugins'):
			if f.endswith('.py'):
				l.append(f[:-3])

		for mod in l:
			try: m = reload(import_module('Plugins.'+mod)).Plugin #So much haxx here
			except AttributeError: continue

			if 'active' in dir(m):
				if not getattr(m, 'active'): continue

			m = m(self.controller)

			for func in dir(m):
				r1 = re.match(r'trigger_(.+)', func)
				r2 = re.match(r'timer_([0-9]+)', func)
				if r1:
					self.triggers[r1.groups(1)[0]] = getattr(m, func)
				elif r2:
					t = int(r2.groups(1)[0])
					timer = self.scheduler.add_interval_task(getattr(m, func), mod+func, 0, t, kronos.method.threaded, [], None)
					self.timers.append(timer)
				elif func == 'on_incoming':
					self.incoming.append(getattr(m, func))
				elif func == 'on_outgoing':
					self.outgoing.append(getattr(m, func))

		if msg:
			self.controller.notice(msg.nick, "Reloaded sucessfully.")

	def on_incoming(self, msg):
		if msg.body.startswith(self.prefix):
			msg.body = msg.body[len(self.prefix):]
			args = msg.body.split()
			command = args.pop(0)
			msg.args = args
			if command in self.triggers:
				self.triggers[command](msg)
			else:
				self.controller.notice(msg.nick, command+' is not a valid command.')
		else:
			for func in self.incoming:
				t_msg = func(msg)
				if t_msg: msg = t_msg
		return msg

	def on_outgoing(self, msg):
		for func in self.incoming:
				t_msg = func(msg)
				if t_msg: msg = t_msg
		return msg



if __name__ == '__main__':
	if len(sys.argv) > 1:
		args = sys.argv[1:]
	else:
		args = []
	
	graphical = not ('nogui' in args)

	if '-s' in args:
		config_filename = args[args.index('-s')+1]
	else:
		config_filename = os.path.join(os.path.expanduser('~'), '.ncssbot_config')

	config = json.loads(open(config_filename, 'rU').read())

	sl = SocketListener(config)

	gui = MainInterface(graphical=graphical)

	controller = Controller(sl, gui, config)

	controller.begin()
