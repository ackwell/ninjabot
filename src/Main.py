'''
Ok, lets get this thing started.
Can i suggest we have the main IRC Protocl in the main package (here), and the site polling/control panel/module system/blah in separate packages?
I'll start putting together the module system, ill put some more details in here on how to call it later :)
'''

import re
import socket
import threading

# constants are here temporarily
# maybe move to a config file in the future
USERNAME = 'NCSSBot'
REALNAME = 'NCSSBot-RN'
DEFAULT_CHANNEL = '#ncss_challenge'
SERVER_HOST = 'roddenberry.freenode.net' # brisbane server
SERVER_PORT = 6667
QUIT_MESSAGE = 'Goodbye!'

class Message:
	UNKNOWN = 0
	CHANNEL = 1
	PRIVATE = 2
	NOTICE = 3
	
	def __init__(self, message):
		if message:
			m = re.match(r'^:(.+?)!([^ ]*) (PRIVMSG|NOTICE) ^([^ ]+) :(.+)$', message)
			if m:
				sender, host, command, destination, body = m.groups()
				
				# find what type of message was sent
				if command == 'PRIVMSG':
					if destination.startswith('#'):
						self.type = Message.CHANNEL
					else:
						self.type = Message.PRIVATE
				else:
					self.type = Message.NOTICE
				
				# since the message class is used to both send and receive,
				# the 'user' property should probably be enough to store the
				# details of the other party, whether it's who we received the
				# message from or who we're sending it to
				self.room = destination # either the channel, or the sender if it's a private message
				self.nick = sender # stores the sender's nick
				self.host = host # the sender's host
				
				# and don't forget to store the body of the message!
				self.body = body
			else:
				# you can't parse an invalid message!!
				raise Exception('Invalid message format.')
		else:
			# no message provided? that's fine!
			# initialise all the vars!
			self.type = Message.UNKNOWN
			self.room = ''
			self.nick = ''
			self.host = ''
			self.body = ''
			
	def __str__(self):
		try:
			if self.type == Message.CHANNEL:
				return 'PRIVMSG %s :%s\r\n' % (self.room, self.body)
			elif self.type == Message.PRIVATE:
				return 'PRIVMSG %s :%s\r\n' % (self.nick, self.body)
			elif self.type == Message.NOTICE:
				return 'NOTICE %s :%s\r\n' % (self.nick, self.body)
			else:
				raise Exception('Cannot generate a message string for an unknown type.')
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
				
				if self.gui: #if running through GUI, log it ready to be polled
					self.LOG.append(msg)
				else:
					print msg
				
				# Firstly, check for ping
				m = re.match(r'^PING :(.+)$', msg)
				if m:
					self.send('PONG :%s\r\n' % m.group(1))
				else:
					pass
		
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

if __name__ == '__main__':
	th = SocketListener()
	th.start()
	while 1:
		try:
			s = raw_input('>')
			# For the moment, simply send a message 's' to the channel
			msg = Message(None)
			msg.type = Message.CHANNEL
			msg.room = DEFAULT_CHANNEL
			msg.body = s
			# send the message
			th.send_message(msg)
		except KeyboardInterrupt:
			break
	
	print
	print 'Waiting for socket thread to terminate... (^C again to force)'
	
	try:
		th.stop()
	except KeyboardInterrupt:
		print
		print 'Forcing termination...'
		exit(0)