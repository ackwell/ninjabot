from common import NinjabotTestCase
import unittest
from unittest.mock import patch, MagicMock


class IRCConnectionTestCase(NinjabotTestCase):
	# a little strange that we must patch it here
	# but, whatever works :)

	@patch('ninjabot.kronos.ThreadedScheduler', MagicMock())
	def setUp(self):
		import ninjabot
		self.connection = ninjabot.IRCConnection()


class TestIRCConnection(IRCConnectionTestCase):
	@patch('asynchat.async_chat.connect')
	@patch('asyncore.loop')
	@patch('ninjabot.IRCConnection.create_socket')
	def test_connect_args_supplied(self, create_socket, loop, connect):
		host, port, nickname, username, realname, password = range(6)

		self.connection.connect(
			host,
			port,
			nickname,
			username,
			realname,
			password
		)

		self.assertEqual(self.connection.host, host)
		self.assertEqual(self.connection.port, port)
		self.assertEqual(self.connection.nickname, nickname)
		self.assertEqual(self.connection.password, password)

		self.assertEqual(self.connection.buffer, '')
		self.assertEqual(self.connection.connected, False)

		import socket
		self.connection.create_socket.assert_called_with(
			socket.AF_INET, socket.SOCK_STREAM)

		connect.assert_called_with(
			(host, port)
		)

		loop.assert_called_with(timeout=0.2)

	@patch('asynchat.async_chat.connect')
	@patch('asyncore.loop')
	@patch('ninjabot.IRCConnection.create_socket')
	def test_connect_args_not_supplied(self, create_socket, loop, connect):
		host, port, nickname = range(3)

		self.connection.username = 'username'
		self.connection.realname = 'realname'

		self.connection.connect(
			host,
			port,
			nickname,
		)

		self.assertEqual(self.connection.username, nickname)
		self.assertEqual(self.connection.realname, nickname)
		self.assertEqual(self.connection.password, '')

	@patch('ninjabot.IRCConnection.nick')
	@patch('ninjabot.IRCConnection.user')
	@patch('ninjabot.IRCConnection.pass_')
	def test_handle_connect_with_password(self, pass_, user, nick):
		self.connection.password = 'password'
		self.connection.nickname = 'nickname'
		self.connection.username = 'username'
		self.connection.realname = 'realname'
		self.connection.handle_connect()

		pass_.assert_called_with('password', now=True)

	@patch('ninjabot.IRCConnection.nick')
	@patch('ninjabot.IRCConnection.user')
	@patch('ninjabot.IRCConnection.pass_')
	def test_handle_connect_without_password(self, pass_, user, nick):
		self.connection.password = None
		self.connection.nickname = 'nickname'
		self.connection.username = 'username'
		self.connection.realname = 'realname'

		self.connection.handle_connect()

		self.assertEqual(self.connection.connected, True)

		self.assertEqual(pass_.called, False)
		nick.assert_called_with('nickname', now=True)
		user.assert_called_with('username', 'realname', now=True)

	@patch('ninjabot.IRCConnection.quit')
	@patch('ninjabot.IRCConnection.handle_close')
	def test_disconnect_whilst_connected(self, handle_close, quit):
		self.connection.connected = True

		self.connection.disconnect('message')

		quit.assert_called_with('message')
		handle_close.assert_called_with()

	@patch('ninjabot.IRCConnection.quit')
	@patch('ninjabot.IRCConnection.handle_close')
	def test_disconnect_whilst_not_connected(self, handle_close, quit):
		self.connection.connected = False

		self.connection.disconnect('message')

		self.assertEqual(quit.called, False)
		self.assertEqual(handle_close.called, False)

	@patch('ninjabot.IRCConnection.close')
	def test_handle_close_without_error(self, close):
		self.connection.handle_close()

		close.assert_called_with()
		self.assertEqual(self.connection.connected, False)

	@patch('ninjabot.IRCConnection.close')
	def test_handle_close_with_error(self, close):
		import socket
		close.side_effect = socket.error

		self.connection.handle_close()

		close.assert_called_with()
		self.assertEqual(self.connection.connected, False)

	def test_irc_send_with_connection_error(self):
		self.connection.connected = False

		import ninjabot
		self.assertRaises(
			ninjabot.ConnectionError,
			self.connection.irc_send,
			('message',)
		)

	def test_irc_send_on_queue(self):
		self.connection.connected = True

		self.connection.irc_send('message', now=False)

		self.assertEqual(
			list(self.connection.message_queue.queue),
			['message']
		)

	@patch('ninjabot.IRCConnection.push')
	def test_irc_send_normal(self, push):
		self.connection.connected = True
		self.connection.irc_send('message', now=True)

		push.assert_called_with(b'message\r\n')

	@patch('ninjabot.IRCConnection.push')
	@patch('ninjabot.IRCConnection.disconnect')
	def test_irc_send_with_socket_error(self, disconnect, push):
		self.connection.connected = True

		import socket
		push.side_effect = socket.error

		self.connection.irc_send('message', now=True)

		disconnect.assert_called_with('Connection reset by peer.')

	@patch('ninjabot.IRCConnection.irc_send')
	def test_send_queue_normal(self, irc_send):
		self.connection.message_queue.put('message')

		self.connection.send_queue()

		irc_send.assert_called_with('message', now=True)

	@patch('ninjabot.IRCConnection.irc_send')
	def test_send_queue_flood(self, irc_send):
		self.connection.message_queue.put('c' * 499)
		self.connection.message_queue.put('at')
		self.connection.message_queue.put('over')

		self.connection.send_queue()

		# "at" is the last message before the flood prevention kicks in
		irc_send.assert_called_with('at', now=True)

	def test_collect_incoming_data(self):
		# the buffer is setup in the IRCConnection.connect method,
		# and we ain't calling that, so we have to set it manually
		self.connection.buffer = ''
		self.connection.collect_incoming_data(b'message')

		self.assertEqual(self.connection.buffer, 'message')

	@patch('ninjabot.Message')
	@patch('ninjabot.IRCConnection.pong')
	def test_found_terminator_pingpong(self, pong, Message):
		self.connection.buffer = 'message'
		Message.return_value.command = 'PING'
		Message.return_value.body = 'body'

		self.connection.found_terminator()

		pong.assert_called_with('body')

	@patch('ninjabot.Message')
	@patch('ninjabot.IRCConnection.message_recieved')
	def test_found_terminator_normal(self, message_recieved, Message):
		self.connection.buffer = 'message'
		Message.return_value.command = 'COMMAND'

		self.connection.found_terminator()

		message_recieved.assert_called_with(Message.return_value)

	def test_message_recieved(self):
		self.assertRaises(
			NotImplementedError,
			self.connection.message_recieved,
			'message'
		)


@patch('ninjabot.IRCConnection.irc_send')
class TestIRCCommands(IRCConnectionTestCase):
	def test_invite(self, irc_send):
		self.connection.invite('nick', 'channel')

		irc_send.assert_called_with('INVITE nick channel', False)

	def test_join_with_key(self, irc_send):
		self.connection.join('channel', 'key')

		irc_send.assert_called_with('JOIN channel key', False)

	def test_join_without_key(self, irc_send):
		self.connection.join('channel')

		irc_send.assert_called_with('JOIN channel', False)

	def test_kick_lists_with_comment(self, irc_send):
		self.connection.kick(
			['chan', 'nell'],
			['user', 'name'],
			'comment'
		)

		irc_send.assert_called_with('KICK chan,nell user,name :comment', False)

	def test_kick_lists_without_comment(self, irc_send):
		self.connection.kick(
			['chan', 'nel'],
			['user', 'name']
		)

		irc_send.assert_called_with('KICK chan,nel user,name', False)

	def test_kick_normal_with_comment(self, irc_send):
		self.connection.kick('channel', 'username', 'comment')

		irc_send.assert_called_with('KICK channel username :comment', False)

	def test_kick_normal_without_comment(self, irc_send):
		self.connection.kick('channel', 'username')

		irc_send.assert_called_with('KICK channel username', False)

	def test_mode_without_params(self, irc_send):
		self.connection.mode('username', 'OP')

		irc_send.assert_called_with('MODE username OP', False)

	def test_mode_with_params(self, irc_send):
		self.connection.mode('username', 'OP', 'PARAMS', False)

		irc_send.assert_called_with('MODE username OP PARAMS', False)

	def test_names_with_list(self, irc_send):
		self.connection.names(['chan', 'nel'])

		irc_send.assert_called_with('NAMES chan,nel', False)

	def test_names_normal(self, irc_send):
		self.connection.names('channel')

		irc_send.assert_called_with('NAMES channel')

	def test_nick(self, irc_send):
		self.connection.nick('username')

		irc_send.assert_called_with('NICK username', False)

	def test_notice_with_list(self, irc_send):
		self.connection.notice(['user', 'name'], 'message')

		irc_send.assert_called_with('NOTICE user,name :message', False)

	def test_notice_without_list(self, irc_send):
		self.connection.notice('username', 'message')

		irc_send.assert_called_with('NOTICE username :message', False)

	# both PING, PONG and PASS are ideally send off right away

	def test_pass_(self, irc_send):
		self.connection.pass_('password')

		irc_send.assert_called_with('PASS password', True)

	def test_ping_with_second_target(self, irc_send):
		self.connection.ping('first', 'second')

		irc_send.assert_called_with('PING first second', True)

	def test_ping_without_second_target(self, irc_send):
		self.connection.ping('first')

		irc_send.assert_called_with('PING first', True)

	def test_pong_with_second_target(self, irc_send):
		self.connection.pong('first', 'second')

		irc_send.assert_called_with('PONG first second', True)

	def test_pong_without_second_target(self, irc_send):
		self.connection.pong('first')

		irc_send.assert_called_with('PONG first', True)

	def test_privmsg_with_list(self, irc_send):
		self.connection.privmsg(['user', 'name'], 'message')

		irc_send.assert_called_with('PRIVMSG user,name :message', False)

	def test_privmsg_normal(self, irc_send):
		self.connection.privmsg('username', 'message')

		irc_send.assert_called_with('PRIVMSG username :message', False)

	def test_quit(self, irc_send):
		self.connection.quit('message')

		irc_send.assert_called_with('QUIT :message', True)

	def test_user(self, irc_send):
		self.connection.user('username', 'realname')

		irc_send.assert_called_with('USER username 0 * :realname', True)



if __name__ == '__main__':
	unittest.main()
