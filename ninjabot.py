import re
import socket

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
	def send(self, message):
		if self.socket is None: raise ConnectionError, "Not connected."

		try:
			message += "\r\n"
			self.socket.sendall(message)
		except socket.error: self.disconnect("Connection reset by peer.")

		# DEBUG
		print "SENT: " + message

	# Recieve data from the server.
	def receive(self):
		try: new_data = self.socket.recv(2**14)
		except socket.error: self.disconnect("Connection reset by peer.")
		if not new_data: self.disconnect("Connection reset by peer.")

		# 'parrently some IRCd don't use the \r in their delimiter
		lines = re.split(r'\r?\n', self.buffer + new_data)
		self.buffer = lines.pop()

		return lines

	def iter_lines(self):
		while self.connected:
			lines = self.receive()
			for line in lines:
				# DEBUG
				print line

				message = Message(line)

				# Handle PINGs
				if message.command == 'PING':
					self.pong(message.body)
					continue

				yield message

	# IRC Commands

	def join(self, channel, key=""):
		self.send("JOIN %s%s" % (channel, key and (" " + key)))

	def nick(self, nickname):
		self.send("NICK " + nickname)

	def pass_(self, password):
		self.send("PASS " + password)

	def ping(self, target, target2=""):
		self.send("PING %s%s" % (target, target2 and (" " + target2)))

	def pong(self, target, target2=""):
		self.send("PONG %s%s" % (target, target2 and (" " + target2)))

	def quit(self, message):
		self.send("QUIT" + (message and (" :" + message)))

	def user(self, username, realname):
		self.send("USER %s 0 * :%s" % (username, realname))




class ninjabot(IRCConnection):
	def __init__(self):
		IRCConnection.__init__(self)

		temp_config = {
			"host": "irc.freenode.net",
			"port": 6667,
			"nickname": "nb_test",
			"username": "nb_test_un",
			"realname": "nb_test_rn"
		}

		self.connect(**temp_config)

		# temp join
		self.join('##ninjabot_test')

		for line in self.iter_lines():
			pass#print line







if __name__ == '__main__':
	t = ninjabot()
