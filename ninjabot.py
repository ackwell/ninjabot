import re
import socket

# Errors
class ConnectionError(Exception):pass

# Apparently some IRCd terminate messages with \n, not \r\n
regexp_line_split = re.compile(r'\r?\n', re.UNICODE)

class IRCConnection:
	def __init__ (self):
		self.host = ''
		self.port = 0

		self.connected = False
		self.buffer = ''

	def connect(self, host, port):
		self.host = host
		self.port = port

		# Get a socket
		self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.soc.connect((self.host, self.port))
		except socket.error:
			self.soc.close()
			raise ConnectionError, "Error connecting to socket."

		# Bits n' pieces we'll use
		self.buffer = ''
		self.connected = True

		# Connect to the server
		# Password shit login whatsit here when required
		#move these to methods
		self.soc.send('NICK nb_test\r\n')
		self.soc.send('USER nb_test 0 * :nb_test_rn\r\n')
		self.soc.send('JOIN :##ninjabot_test\r\n')

	def recieve(self):
		self.buffer += self.soc.recv(2**14)
		lines = regexp_line_split.split(self.buffer)
		self.buffer = lines.pop()

		for line in lines:
			print line
			m = re.match(r'^PING :(.+)$', line)
			if m:
					self.soc.send('PONG :%s\r\n' % m.group(1))










if __name__ == '__main__':
	t = IRCConnection()
	t.connect('irc.freenode.net', 6667)

