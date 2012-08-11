from Tkinter import * #@UnusedWildImport
from Main import * #@UnusedWildImport

import time

#Formatting
DEFAULT = {
"state":DISABLED,
"bg":"#DDDDDD",
"width":1,
"height":1,
"wrap":WORD,
"font":"courier 10"
}

STYLES = {

"NOTICE": {
"foreground":"#E50000"
},

"PRIVMSG": { #this is only used for /msg
"foreground":"#0000E5"
},

"JOIN": {
"foreground":"#2A8C2A"
},

"PART": {
"foreground":"#66361F"
},

"QUIT": {
"foreground":"#66361F"
},

"MODE": {
"foreground":"#80267F"
},

"NICK": {
"foreground":"#007F7F"
}

}

class MainInterface(Frame):

    def __init__(self, graphical=True):
        self.controller = None
        self.graphical = graphical
        self.should_stop = False
        self.exit_status = 0

        if self.graphical:
            #Init main frame
            Frame.__init__(self, bg="#CCCCCC", width=640, height=480)
            self.pack_propagate(0)
            self.pack(expand=YES, fill=BOTH)
            self.master.title("NCSSBot GUI")

            #TK-Frame: To relieve packing order nightmares
            self.log_frame = Frame(self)
            self.inp_frame = Frame(self)

            #TK-Text: Widget for logging
            self.log = Text(self.log_frame, DEFAULT)

            #TK-Scrollbar for Text widget
            self.log_scroll = Scrollbar(self.log_frame)

            #TK-Entry: Input field
            self.inp_field = Entry(self.inp_frame)

            #TK-Button:  Why not :)
            self.send_button = Button(self.inp_frame, text="Send", width=8, command=self.SendPressed)

            #Link the scrollbar
            self.log.configure(yscrollcommand=self.log_scroll.set)
            self.log_scroll.configure(command=self.log.yview)

            #Pack GUI Frames
            self.log_frame.pack(expand=YES, fill=BOTH, side=TOP)
            self.inp_frame.pack(fill=X, side=TOP)

            #Pack GUI elements into frames
            self.log.pack(expand=YES, fill=BOTH, side=LEFT)
            self.log_scroll.pack(side=RIGHT, fill=Y)
            self.inp_field.pack(expand=YES, fill=BOTH, side=LEFT)
            self.send_button.pack(expand=NO, side=LEFT)

            #Bind enter to do same job as the send button
            self.inp_field.bind("<Return>", self.EnterPressed)

            #Set up the the formatting tags:
            #self.log.tag_configure("private", PRIVATE)

            for key, value in STYLES.items():
                self.log.tag_configure(key, value)

    def EnterPressed(self, event):
        self.SendPressed()

    def SendPressed(self):
        msg = self.inp_field.get()
        self.inp_field.delete(0, END)
        self.SendMsg(msg)

    def SendMsg(self, data): #modify later to run command
        if self.controller:
            if data == '/quit':
                self.controller.die()
            else:
                msg = Message()
                msg.type = Message.CHANNEL
                msg.command = Message.PRIVMSG
                msg.channel = self.controller.config['server']['channel']
                msg.nick = self.controller.config['config']['nick']
                msg.body = data
                self.controller.outgoing_message(msg)


    def display_messages(self):
        buff = self.controller.buffer
        if len(buff) < 1:
            return
        for msg in buff:
            if self.graphical:
                self.log['state'] = NORMAL #enable edting

                if self.log.index('end-1c')!='1.0' and not msg.command.isdigit():
                    self.log.insert(END, '\n') #insert a new line

                if msg.command == Message.PRIVMSG:
                    if msg.type == Message.CHANNEL:
                        self.log.insert(END, msg.nick.rjust(18) + ': ')

                    elif msg.type == Message.PRIVATE:
                        self.log.insert(END, ' '*(16-len(msg.nick)) + '>')
                        self.log.insert(END, msg.nick, msg.command)
                        self.log.insert(END, '<: ')

                    self.log.insert(END, msg.body)
                    if msg.ctcp:
                        self.log.insert(END, ' (CTCP: '+msg.ctcp+')')

                elif msg.command == Message.NOTICE:
                    self.log.insert(END, ' '*(16-len(msg.nick)) + '-')
                    self.log.insert(END, msg.nick, msg.command)
                    self.log.insert(END, '-: ')
                    self.log.insert(END, msg.body)

                elif msg.command == Message.JOIN:
                    self.log.insert(END, " *-* "+msg.nick+" has joined "+msg.body, msg.command)

                elif msg.command == Message.PART:
                    self.log.insert(END, " *-* "+msg.nick+" has left "+msg.channel+" ("+msg.body+")", msg.command)

                elif msg.command == Message.QUIT:
                    self.log.insert(END, " *-* "+msg.nick+" has quit ("+msg.body+")", msg.command)

                elif msg.command == Message.MODE:
                    self.log.insert(END, " *-* "+msg.nick+" has set mode "+msg.body+" on "+msg.channel, msg.command)

                elif msg.command == Message.NICK:
                    self.log.insert(END, " *-* "+msg.nick+" has changed nick to "+msg.body, msg.command)

                self.log['state'] = DISABLED #disable editing
                self.log.yview(END) #scroll down
            else:
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
        #clear the buffer
        self.controller.buffer = []


    def clock(self):
        self.display_messages()

        self.after(500, self.clock)

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
        if self.graphical:
            #initiate the buffer check
            self.after(500, self.clock)

            #start the loop
            self.mainloop()
        else:
            while not self.should_stop:
                try:
                    time.sleep(1)
                except KeyboardInterrupt:
                    break

        print 'Exiting on GUI thread with status %d' % self.exit_status
        sys.exit(self.exit_status)

#If run as main app, start up the GUI
if __name__ == "__main__":
    pass
