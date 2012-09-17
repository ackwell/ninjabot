from Main import *

import time

class CLInterface:
    def __init__(self):
        self.controller = None
        self.should_stop = False
        self.exit_status = 0

    def display_messages(self):
        buff = self.controller.buffer
        if len(buff) < 1:
            return
        for msg in buff:
            if msg.command == Message.PRIVMSG:
                print msg.channel + ' <' + msg.nick + '>: ' + msg.body
            elif msg.command == Message.NOTICE:
                print 'NOTICE <' + msg.nick + '>: ' + msg.body
            elif msg.command == Message.JOIN:
                print ' *-* ' + msg.nick + ' has joined ' + msg.body
            elif msg.command == Message.PART:
                print ' *-* ' + msg.nick + ' has left ' + msg.channel + ' (' + msg.body + ')'
            elif msg.command == Message.QUIT:
                print ' *-* ' + msg.nick + ' has quit ' + msg.channel + ' (' + msg.body + ')'
            elif msg.command == Message.MODE:
                print ' *-* ' + msg.nick + ' has set mode ' + msg.body + ' on ' + msg.channel
            elif msg.command == Message.NICK:
                print ' *-* ' + msg.nick + ' has changed nick to ' + msg.body
        self.controller.buffer = []

    def stop(self, status):
        self.should_stop = True
        self.exit_status = status
        try:
            self.destroy()
        except:
            pass
        try:
            self.quit()
        except:
            pass

    def startloop(self):
        while not self.should_stop:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break

        print 'Exiting on CLI thread with status %d' % self.exit_status
        sys.exit(self.exit_status)
