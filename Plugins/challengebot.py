# NCSS Challenge Plugin

from apis import ncss
import json
import os
import time

# I've moved config to self.controller.config. It's read from ~/.ncssbot_config by default, but can be redirected with the -c flag. Gimme a yell and i'll send you my config file.

class Plugin:
    def __init__(self, controller, config):
        self.controller = controller

        # read config file
        self.cookie = config['cookie']
        self.course = config['course'])
        self.channel = ','.join(self.controller.config['bot']['channels'])

        # create NCSS object
        self.ncss = ncss.NCSS(course=self.course, cookie=self.cookie)

        # set up delta variables
        self.old_forums = dict()
        self.old_students = None

        # Congrats plugin stuff
        # Beginner/Intermediate
        self.congrats_beg_int = False
        self.time_beg_int     = 1347188400
        self.message_beg_int  = 'The NCSS Challenge is now over for those in the Beginners and Intermediate streams! Congratulations to all who participated!'
        # Advanced
        self.congrats_adv     = False
        self.time_adv         = 1347199200
        self.message_adv      = 'The NCSS Challenge is now over for those in the Advanced stream! Congratulations to all who participated!'

    # challenge poll
    def timer_60(self):
        # update forums
        for forum_id in self.ncss.get_forum_list():
            forum = self.ncss.get_forum(forum_id)
            if forum:
                title, new_threads = forum

                if forum_id in self.old_forums:
                    old_threads = self.old_forums[forum_id]

                    # generate delta
                    added, updated = ncss.generate_forum_delta(old_threads, new_threads)
                    added_count, updated_count = len(added), len(updated)

                    if added_count or updated_count:
                        # compile a message
                        statuses = list()
                        if added_count:
                            status = '%d new post' % added_count
                            if added_count > 1:
                                status += 's'
                            status += ' (%s)' % ', '.join(added)
                            statuses.append(status)
                        if updated_count:
                            status = '%d updated post' % updated_count
                            if updated_count > 1:
                                status += 's'
                            status += ' (%s)' % ', '.join(updated)
                            statuses.append(status)
                        message = '%s: %s' % (title, ', '.join(statuses))

                        # send message
                        self.controller.privmsg(self.channel, message)

                # add threads to dictionary for next polling
                self.old_forums[forum_id] = new_threads

        # update leaderboard
        new_students = self.ncss.get_students()
        if new_students:
            old_students = self.old_students
            self.old_students = new_students

            if old_students:
                # generate delta
                delta = ncss.generate_students_delta(old_students, new_students)
                names = sorted(delta.keys(), cmp=lambda a, b: cmp(a.split(' ', 1)[1], b.split(' ', 1)[1]))
                for name in names:
                    score, status = delta[name]
                    msg = None
                    if status == ncss.ADDED:
                        msg = '%s is now on the leaderboard with %d points!' % (name, score)
                    elif status == ncss.CHANGED:
                        change = new_students[name] - old_students[name]
                        msg = '%s has gained %d points for a new total of %d!' % (name, change, score)
                    if msg:
                        self.controller.privmsg(self.channel, msg)
                    msg = None
                    if status == ncss.ADDED or status == ncss.CHANGED:
                        if score > 200:
                            msg = 'Congratulations to %s on completing this year\'s challenge!' % name.split(' (')[0]
                    if msg:
                        self.controller.privmsg(self.channel, msg)

        # Congrats plugin
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
