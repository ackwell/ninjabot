import random

class Plugin:

    #modes
    INACTIVE = 0
    PLAYING = 1
    
    DICT_PATH = "dictionary.txt"
    CONS = "bcdfghjklmnpqrstvwxyz"
    VOWELS = "aeiou"


    def __init__(self, controller, config):
        self.c = controller
        self.mode = self.INACTIVE
        self.timer = 0
        
    def trigger_word(self, msg):
        "Letters and numbers inspired wordgame for IRC. For detailed help, run `word help`"
        if not self.mode:
            if len(msg.args) == 0:
                self.c.notice(msg.nick, "Please specify a wordgame command. Check `%sword help` for avaliable commands."%self.c.command_prefix)
                return

            command = msg.args[0].lower()
            if 'word_'+command in dir(self):
                getattr(self, 'word_'+command)(msg)
            else:
                self.c.notice(msg.nick, "The command '%s' does not exist. Check `%sword help` for avalable commands."%(command, self.c.command_prefix))
                
        else: #there's a game underway, check the word
            print msg.args[0].lower(), msg.nick
            self._take_word(msg.args[0].lower(), msg.nick)
            
    def word_help(self, msg):
        "Prints the help text. Further command help can be displayed by specifng a command."
        if len(msg.args) == 0:
            self.c.notice(msg.nick, 'An IRC implementation of letters and numbers word game. Try and make the longest word.')
            com = ''
            for d in dir(self):
                if d.startswith('word_'):
                    com += '%s%s '%(self.c.command_prefix, d.split('_')[1])
            self.c.notice(msg.nick, 'Avaliable commands are: %s.'%com)
            self.c.notice(msg.nick, 'For more information, run `%sword help <command>`.'%self.c.command_prefix)
        else:
            try: self.c.notice(msg.nick, getattr(self, 'word_'+msg.args[0]).__doc__)
            except AttributeError: self.c.notice(msg.nick, "That command does not exist. For a list of commands, run %sword help."%self.c.command_prefix)

    def word_start(self, msg):
        "Starts a wordgame!"
        if self.mode:
            self.c.notice(msg.nick, "There is already a wordgame running!")
            return
        
        self.best_word = ["",""]
        self.originals = []
        
        j = random.randint(1,5) #Select a random number of vowels, cons
        for i in range(j):
            self.originals.append(random.choice(self.VOWELS))
        for i in range(10-j):
            self.originals.append(random.choice(self.CONS))
        
        self.mode = self.PLAYING
        self.timer = 3
        self.start_player = msg.nick
        self.channel = msg.channel
        self.c.privmsg(self.channel, "A new wordgame begins! The Letters are: %s"%"".join(self.originals))
        self.best_possible = self._find_best()
            
        

    def word_stop(self, msg):
        "Stops the current wordgame. Only admins and the start player can stop a game."
        if not (self.c.is_admin(msg.nick, True) or msg.nick == self.start_player):
            self.c.notice(msg.nick, "Only ops+ and the start player can stop a game.")
            return
        elif self.mode == self.self.INACTIVE:
            self.c.notice(msg.nick, "There is no game in progress.")
            return
            
        self._finished()
    
    def word_add(self, msg):
        if not (self.c.is_admin(msg.nick, True)):
            return
        
        word = msg.args[0].lower()
        with open(self.DICT_PATH, 'a') as file:
            file.write(word+"\n")

    def timer_10(self):
        if self.mode == self.PLAYING:
            if self.timer > 0:
                if self.timer == 1:
                    self.c.privmsg(self.channel, "%d seconds left! Best word so far: %s"%(10*self.timer,self.best_word[0]))
                self.timer -= 1
            else:
                self._finished()
                
    def _find_best(self):
        best = ""
        with open(self.DICT_PATH, 'r') as inF:
            for line in inF:
                word = line.strip()
                letters = self.originals[::]
                try:
                    for l in word:
                        letters.remove(l)
                except ValueError:
                    continue
                if len(word) > len(best):
                    best = word
        return best
                
    
    def _finished(self):
        self.takingWords = False
        if self.best_word[0] == "":
            self.c.privmsg(self.channel, "Game over! Nobody got a word.")
        else:
            self.c.privmsg(self.channel, "Game over! Best word was '%s' by %s."%(self.best_word[0], self.best_word[1]))
        self.c.privmsg(self.channel, "Best possible word was '%s'."%self.best_possible)

        self.start_player = ''
        self.mode = self.INACTIVE
            
    def _take_word(self, word, user):
        letters = self.originals[::]
        for letter in word:
            if letter in self.originals and letter in letters:
                letters.remove(letter)
                continue
            else:
                return
        print "Passed letter check"
        if len(word) > len(self.best_word[0]):
            print "Searching for word",
            with open(self.DICT_PATH, 'r') as inF:
                for line in inF:
                    if line.strip() == word:
                        print "Found."
                        self.best_word[0] = word
                        self.best_word[1] = user
                        self.c.privmsg(self.channel, "Best word so far: %s"%self.best_word[0])
                        return
                

