import random

class Plugin:

    #modes
    INACTIVE = 0
    PLAYING = 1

    DICT_PATH = "dictionary.txt"
    CONS = "bcdfghjklmnpqrstvwxyz"
    VOWELS = "aeiou"
    WORD_SIZE = 10
    MIN_BASE = 6

    def __init__(self, controller, config):
        self.c = controller
        self.mode = self.INACTIVE
        self.timer = 0
	self.found = []

    def _is_good(self, word):
        "Checks if a word is in the current running game word"
	if self.mode == self.INACTIVE or len(word) > len(self.originals):
		return False

	letters = self.originals[:]
	for letter in word:
		if letter in letters:
			letters.remove(letter)
		else:
			return False

	return True

    def trigger_word(self, msg):
        "Letters and numbers inspired wordgame for IRC. For detailed help, run `word help`"
	command = msg.args[0].lower()

	# Commands are only commands if the game is not running or if the wor is a function, has been found or is not a valid word
        if not self.mode or ("word_"+command in dir(self) and (command in self.found or not self._is_good(command))):
            if len(msg.args) == 0:
                self.c.notice(msg.nick, "Please specify a wordgame command. Check `%sword help` for avaliable commands."%self.c.command_prefix)
                return

	    del msg.args[0]
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
            self.c.notice(msg.nick, 'An IRC implementation of letters and numbers word game. Try and make the longest word. Use %sword <word>'%self.c.command_prefix)
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
	self.found = []
        self.originals = []

	# Get a "base word" to use (minimum length of self.MIN_BASE)
	dictionary = open(self.DICT_PATH, "r")
	words = dictionary.readlines()

	base_word = random.choice(words).strip()
	while len(base_word) < self.MIN_BASE:
		base_word = random.choice(words).strip()

	dictionary.close()

	# Add some random letters to it, if it is too small
	if len(base_word) < self.WORD_SIZE:
		for new in xrange(self.WORD_SIZE - len(base_word)):
			# Choose randomly between consonants and vowels
			base_word += random.choice(self.CONS + self.VOWELS)

	# Turn word into list and shuffle it
	self.originals = list(base_word)
	random.shuffle(self.originals)

        self.mode = self.PLAYING
        self.timer = 3
        self.start_player = msg.nick
        self.channel = msg.channel
        self.best_possible = self._find_best()

        self.c.privmsg(self.channel, "A new wordgame begins! The Letters are: %s (best word is %d letters long)"%("".join(self.originals), len(self.best_possible)))

    def word_stop(self, msg):
        "Stops the current wordgame. Only admins and the start player can stop a game."
        if not (self.c.is_admin(msg.nick, True) or msg.nick == self.start_player):
            self.c.notice(msg.nick, "Only ops+ and the start player can stop a game.")
            return
        elif self.mode == self.INACTIVE:
            self.c.notice(msg.nick, "There is no game in progress.")
            return

        self._finished()

    def word_add(self, msg):
        "Add <word> to the wordgame dictionary. Only admins may do this."
        if not (self.c.is_admin(msg.nick, True)):
            return

        word = msg.args[0].lower()
        with open(self.DICT_PATH, 'a') as file:
            file.write(word+"\n")

    def timer_10(self):
        if self.mode == self.PLAYING:
            if self.timer > 0:
		if self.best_word[0]:
		    self.c.privmsg(self.channel, "%d seconds left! Best word so far: %s"%(10*self.timer,self.best_word[0]))
		else:
		    self.c.privmsg(self.channel, "%d seconds left! No words so far."%(10*self.timer))
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
        if word in self.found:
            self.c.privmsg(self.channel, "The word %s had already been found" % word)
	    return

	if not self._is_good(word):
		return

	self.found.append(word)

        if len(word) > len(self.best_word[0]):
            with open(self.DICT_PATH, 'r') as inF:
                for line in inF:
                    if line.strip() == word:
                        self.best_word[0] = word
                        self.best_word[1] = user
                        self.c.privmsg(self.channel, "Best word so far: %s"%self.best_word[0])
                        return


