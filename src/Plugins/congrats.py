import time
from apis import ncss

class Plugin:
    active = True

    def __init__(self, controller):
        self.controller       = controller
        self.cookie           = self.controller.config['ncss']['cookie']
        self.course           = int(self.controller.config['ncss']['course'])
        self.ncss             = ncss.NCSS(course=self.course, cookie=self.cookie)
        # Beginner/Intermediate
        self.congrats_beg_int = False
        self.time_beg_int     = 1347188400
        self.message_beg_int  = 'The NCSS Challenge is now over for those in the Beginners and Intermediate streams! Congratulations to all who participated!'
        # Advanced
        self.congrats_adv     = False
        self.time_adv         = 1347199200
        self.message_adv      = 'The NCSS Challenge is now over for those in the Advanced stream! Congratulations to all who participated!'

    def timer_53(self):
        now = time.time()
        if not self.congrats_beg_int and now > self.time_beg_int:
            self.congrats_beg_int = True
            self.controller.privmsg(self.controller.channel, self.message_beg_int)

        if not self.congrats_adv and now > self.time_adv:
            self.congrats_adv = True
            self.controller.privmsg(self.controller.channel, self.message_adv)
            
            results = self.ncss.get_students()
            names   = sorted(results.keys(), cmp=lambda a, b: cmp(a.split(' ', 1)[1], b.split(' ', 1)[1]))
            
            specialmsg   = 'A special congratulations goes to those that finished all the tasks:'
            specialnames = [ x.split(' (')[0] for x in names if 200 < results[x] < 210 ]
            
            self.controller.privmsg(self.controller.channel, specialmsg)
            self.controller.privmsg(self.controller.channel, '%s and %s.' % (', '.join(specialnames[:-1]) ,specialnames[-1]))

            speshulmsg = 'A \002special\002 congratulations also to those who not only finished all the tasks, but scored full points while doing so:'
            speshulnames = [ x.split(' (')[0] for x in names if results[x] == 210 ]

            self.controller.privmsg(self.controller.channel, speshulmsg)
            self.controller.privmsg(self.controller.channel, '%s and %s.' % (', '.join(speshulnames[:-1]) ,speshulnames[-1]))
