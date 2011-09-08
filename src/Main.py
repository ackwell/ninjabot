'''
Ok, lets get this thing started.
Can i suggest we have the main IRC Protocl in the main package (here), and the site polling/control panel/module system/blah in separate packages?
I'll start putting together the module system, ill put some more details in here on how to call it later :)
'''

import re
import socket
import sys
import threading

from Interface import *

# constants are here temporarily
# maybe move to a config file in the future
USERNAME = 'NCSSBot'
REALNAME = 'NCSSBot-RN'
DEFAULT_CHANNEL = '#ncsstest'
SERVER_HOST = 'roddenberry.freenode.net' # brisbane server
SERVER_PORT = 6667
QUIT_MESSAGE = 'Goodbye!'

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

			if message[0] == ':':
				prefix, message = message[1:].split(' ', 1)
			
			if message.find(' :') != -1:
				message, trailing = message.split(' :', 1)
				args = message.split()
				args.append(trailing)
			else:
				args = message.split()
			
			self.command = args.pop(0)

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
			
			if len(args) == 2:
				self.channel, self.body = args
			elif len(args) == 1:
				self.channel = args[0]
				self.body = ''
			else:
				self.channel = ''
				self.body = ''

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
			
	def __str__(self):
		try:
			return '%s %s :%s\r\n' % (self.command, self.channel, self.body)
		except NameError:
			raise Exception('One or more required properties were not set on the Message object')

class SocketListener(threading.Thread):
	#List used to store logs when GUI is being used
	#GUI checks this list every second
	LOG = []
	
	def __init__(self, gui = False):
		self.gui = gui
		
		# Initialise the socket and connect
		# Also set the socket to non-blocking, so if there is no data to
		# read, the .recv() operation will not hang
		self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self._sock.connect((SERVER_HOST, SERVER_PORT))
		self._sock.setblocking(False)
		
		# Initialise some vars
		self._stop = False
		self._stopped = False
		self._write_buffer = []
		
		# Initialise the superclass
		threading.Thread.__init__(self)
	
	def run(self):
		# Send our love to the server
		self._sock.send('NICK %s\r\n' % USERNAME)
		self._sock.send('USER %s 0 * :%s\r\n' % (USERNAME, REALNAME))
		self._sock.send('JOIN :%s\r\n' % DEFAULT_CHANNEL)
		
		# Initialise the read buffer
		read_buffer = ''
		while not self._stop:
			# Write bytes as needed
			while len(self._write_buffer) > 0:
				self._sock.send(self._write_buffer[0])
				del self._write_buffer[0]
			
			# Read bytes as needed
			try:
				read_buffer += self._sock.recv(1)
			except socket.error:
				continue
			
			# Check whether we've formed a complete message
			if read_buffer.endswith('\r\n'):
				msg = read_buffer[:-2]
				read_buffer = ''
				
				#if self.gui: #if running through GUI, log it ready to be polled
				#	self.LOG.append(msg)
				#else:
				#	print msg
				
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
						print e, msg

		
		# Once we are told to stop, send the quit message, close the socket,
		# and end the thread
		self._sock.send('QUIT :%s\r\n' % QUIT_MESSAGE)
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
		self.send(str(msg))

class Controller:
	def __init__(self, sl, gui):
		# Give ourselves a reference to the SocketListener & GUI
		self.sl = sl
		self.gui = gui

		# And give our own reference to them
		self.sl.controller = self
		self.gui.controller = self

		self._should_die = False
	
	def begin(self):
		# Start the SocketListener
		self.sl.start()
		self.gui.mainloop()

		self.sl.stop()

	def incoming_message(self, msg):
		# Received message object from the sl
		# Parse it and display it in the gui
		self.gui.display_message(msg)
	
	def outgoing_message(self, msg):
		# Received message object
		# Send it through the sl and to the gui for displaying
		self.sl.send_message(msg)
		self.gui.display_message(msg)
	
	def die(self):
		self.sl.stop()
		quit()

if __name__ == '__main__':
	if len(sys.argv) > 1:
		args = sys.argv[1:]
	else:
		args = []
	
	graphical = not ('nogui' in args)

	sl = SocketListener()

	gui = MainInterface(graphical=graphical)

	controller = Controller(sl, gui)

	controller.begin()
