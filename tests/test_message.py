import os
import unittest


with open(os.path.join(os.path.dirname(__file__), 'test_message_data.txt')) as fh:
    TEST_MESSAGE_DATA = fh.readlines()


class TestMessage(unittest.TestCase):
    def test_init_privmsg(self):
        from ninjabot import Message

        # import pudb
        # pu.db

        message_data = ':Nickname!username@hostname COMMAND channel_name :trailing'
        instance = Message(message_data)

        self.assertEqual(instance.command, 'COMMAND')
        self.assertEqual(instance.channel, 'channel_name')
        self.assertEqual(instance.body, 'trailing')
        self.assertEqual(instance.data, [])
        self.assertEqual(instance.nick, 'Nickname')
        self.assertEqual(instance.user, 'username')
        self.assertEqual(instance.host, 'hostname')
        self.assertEqual(instance.ctcp, '')
        self.assertEqual(instance.type, Message.OTHER)

    def test_ctcp_dequote(self):
        pass

if __name__ == '__main__':
    unittest.main()
