# Regex Plugin for NCSSBot

from collections import defaultdict, deque
import re

BACKLOG = 3 # keep this many past messages saved for each user

last_messages = defaultdict(deque)

class Plugin:
    def __init__(self, controller):
        self.controller = controller

    def on_incoming(self, msg):
        if msg.type == msg.CHANNEL:
            # check if the message matches the s/blah/blah/ syntax
            # regex could have been used for this, but factoring in those escaped forward slashes
            # would have been more trouble than it was worth...
            body = msg.body
            their_messages = last_messages[msg.nick]

            groups = list()
            current_group = ''
            for i in range(len(body)):
                if i == 0 and body[i] != 's':
                    break
                elif i == 1 and body[i] != '/':
                    break
                elif body[i] == '/' and (body[i-1] != '\\' or (len(body) >= 3 and body[i-2] == '\\')):
                    groups.append(current_group)
                    current_group = ''
                else:
                    current_group += body[i]
            else:
                if len(current_group) == 0 and len(groups) == 3:
                    # did they have a last message?
                    if msg.nick in last_messages:
                        _, pattern, replacement = map(lambda s: s.replace('\\/', '/'), groups)

                        # scan for a matching message in their last messages
                        for message in their_messages:
                            try: # will treat the regex as a normal message if an error occurs, i.e. invalid syntax
                                if re.search(pattern, message):
                                    body = re.sub(pattern, replacement, message)

                                    # send it
                                    self.controller.privmsg(msg.channel, '%s meant to say: %s' % (msg.nick, body))
                                    break
                            except:
                                pass
                        else:
                        	# match wasn't found
                        	# return without adding this to their last messages
                        	return

            # add it to the last messages dictionary
            their_messages = last_messages[msg.nick]
            their_messages.appendleft(body)
            if len(their_messages) > BACKLOG:
                their_messages.pop()
