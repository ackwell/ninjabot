# NCSS Challenge Plugin

from apis import ncss
import json
import os

# I've moved config to self.controller.config. It's read from ~/.ncssbot_config by default, but can be redirected with the -c flag. Gimme a yell and i'll send you my config file.

class Plugin:
    active = True

    # This is the init for the plugin. All plugins are initiated when the bot is booted up.
    # If/when I implement a reload function, plugins would be re-initiated when reloaded.
    # It's probably a good idea to store a reference to the controller here, you'll need it
    # to utilise the bot's functions.
    def __init__(self, controller):
        self.controller = controller

        # read config file
        #config = json.loads(open(config_filename, 'rU').read())
        self.cookie = self.controller.config['ncss']['cookie']
        self.course = int(self.controller.config['ncss']['course'])
        self.channel = self.controller.config['server']['channel']

        # create NCSS object
        self.ncss = ncss.NCSS(course=self.course, cookie=self.cookie)

        # set up delta variables
        self.old_forums = dict()
        self.old_students = None

    #I just got rid of the incoming/outgoing hooks, it just clutters up the arrays and stuff.

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
