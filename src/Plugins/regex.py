# Regex Plugin for NCSSBot

import re

last_messages = dict()

class Plugin:
    def __init__(self, controller):
        self.controller = controller
    
    def on_incoming(self, msg):
        if msg.type == msg.CHANNEL:
            # check if the message matches the s/blah/blah/ syntax
            # regex could have been used for this, but factoring in those escaped forward slashes
            # would have been more trouble than it was worth...
            body = msg.body
            groups = list()
            current_group = ''
            for i in range(len(body)):
                if i == 0 and body[i] != 's':
                	break
                elif i == 1 and body[i] != '/':
                    break
                elif body[i] == '/' and body[i-1] != '\\':
                    groups.append(current_group)
                    current_group = ''
                else:
                	current_group += body[i]
            else:
            	if len(current_group) == 0 and len(groups) == 3:
                    # did they have a last message?
                    if msg.nick in last_messages:
                        last_message = last_messages[msg.nick]

                        _, pattern, replacement = map(lambda s: s.replace('\\/', '/'), groups)

                        # perform regex
                        body = re.sub(pattern, replacement, last_message)
                        
                        # send it
                        self.controller.privmsg(msg.channel, '%s meant to say: %s' % (msg.nick, body))

            # add it to the last messages dictionary
            last_messages[msg.nick] = body
