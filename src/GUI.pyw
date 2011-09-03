from Tkinter import * #@UnusedWildImport
from Main import * #@UnusedImport
from Parse import * #@UnusedWildImport

#Formatting
DEFAULT = {
"state":DISABLED,
"bg":"#DDDDDD",
"width":1,
"height":1,
"wrap":WORD,
"font":"courier 10"
}

NOTICE = {
"foreground":"#E50000"
}

PRIVATE = {
"foreground":"#0000E5"
}

JOIN = {
"foreground":"#2A8C2A"
}

PART = {
"foreground":"#66361F"
}

QUIT = PART

MODE = {
"foreground":"#80267F"
}

class MainInterface(Frame):
    
    def __init__(self):
        #Init main frame
        Frame.__init__(self, bg="#CCCCCC")
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
        self.log.tag_configure("private", PRIVATE)
        self.log.tag_configure("notice", NOTICE)
        self.log.tag_configure("join", JOIN)
        self.log.tag_configure("part", PART)
        self.log.tag_configure("quit", QUIT)
        self.log.tag_configure("mode", MODE)
    
    def EnterPressed(self, event):
        self.SendPressed()
    
    def SendPressed(self):
        msg = self.inp_field.get()
        self.inp_field.delete(0, END)
        self.SendMsg(msg)
    
    def SendMsg(self, msg): #modify later to run command
        pass
        
    
    def Log(self, msg): #this will need some srs modification
        #numlines = self.log.index('end - 1 line').split('.')[0]
        self.log["state"] = NORMAL #enable edting
        
        #parse the message
        p = parse_msg(msg)
        
        if self.log.index('end-1c')!='1.0' and not p["cmd"].isdigit():
            self.log.insert(END, '\n') #insert a new line
        
        
        nick = get_nick(p["pfx"])
        print p
        if p["cmd"] == "PRIVMSG": #channel/PM
            if p["args"][0] == USERNAME: #Private message
                self.log.insert(END, " "*(16-len(nick))+">")
                self.log.insert(END, nick, "private")
                self.log.insert(END, "<: ")
                
            else: #Channel message
                self.log.insert(END, nick.rjust(18)+": ")
            self.log.insert(END, p["args"][-1])
        
        elif p["cmd"] == "NOTICE":
            self.log.insert(END, " "*(16-len(nick))+"-")
            self.log.insert(END, nick, "notice")
            self.log.insert(END, "-: ")
            self.log.insert(END, p["args"][-1])
        
        elif p["cmd"] == "JOIN":
            self.log.insert(END, " *-* "+nick+" has joined "+p["args"][0], "join")
        
        elif p["cmd"] == "PART":
            self.log.insert(END, " *-* "+nick+" has left "+p["args"][0]+" ("+p["args"][-1]+")", "part")
            
        elif p["cmd"] == "QUIT":
            self.log.insert(END, " *-* "+nick+" has quit ("+p["args"][-1]+")", "quit")
        
        elif p["cmd"] == "MODE":
            self.log.insert(END, " *-* "+nick+" has set mode "+p["args"][-1]+" on "+p["args"][0], "mode")
        
        self.log['state'] = DISABLED #disable editing
        self.log.yview(END) #scroll down
    
    def checkLog(self):
        if len(SL.LOG)>0: #if there is somthing to grab
            for msg in SL.LOG:
                self.Log(msg)
            SL.LOG = []

def update():
    gui.checkLog()
    
    #loop back every 1 second
    gui.after(1000, update)
    
    
#If run as main app, start up the GUI
if __name__ == "__main__":
    
    gui = MainInterface()
    
    SL = SocketListener(True)
    SL.start()
    
    #start the update loop
    gui.after(1000,update())
    
    #and start the GUI loop
    gui.mainloop()
    
    #Whn the GUI is closed, kill the SocketListener
    SL.stop()