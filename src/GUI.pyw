from Tkinter import * #@UnusedWildImport
from Main import SocketListener

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
        self.log = Text(self.log_frame, state=DISABLED, width=1, height=1, bg="#DDDDDD", wrap=NONE)
        
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
        
        #Set up the Bot's framework
        self.SL = SocketListener(self)
        #self.SL.start()
    
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
        self.log["state"] = NORMAL
        if self.log.index('end-1c')!='1.0':
            self.log.insert(END, '\n')
        self.log.insert(END, msg)
        self.log['state'] = DISABLED
        self.log.yview(END)



#If run as main app, start up the GUI
if __name__ == "__main__":
    gui = MainInterface()
    
    gui.mainloop()