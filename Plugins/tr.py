# tr Plugin for ninjabot

import re

last_messages = {}

class Plugin:
    def __init__(self, controller, config):
        self.controller = controller

    def on_incoming(self, msg):
        # Ignore those who have been ignored...
        if self.controller.is_ignored(msg.nick):return

        if msg.type != msg.CHANNEL:return

        body = msg.body

        # check if the message matches the (y|tr)/blah/blah/ syntax
        matches = re.match(r'''(?x)     # verbose mode
                    ^(?:y|tr)(/)        # starts with y/ or tr/
                    (
                        (?:\\\1)*       # any number of escaped /
                        [^/]+           # at least 1 non-/
                        (?:\\\1[^/]*)*  # an escaped / and any number of non-/, repeatedly
                    )
                    /                   # literal /
                    ((?:\\\1)*[^/]+(?:\\\1[^/]*)*) # the above again
                    /?$                 # end with optional /
                ''', body)

        if matches:
            groups = matches.groups()
            # did they have a last message?
            if msg.nick in last_messages:
                last_message = last_messages[msg.nick]
                if len(groups) == 2:
                    pattern, replacement = [s.replace('\\'+groups[0], groups[0]) for s in groups][1:]
                    if len(pattern) == len(replacement):
                        body = last_message.translate(dict(zip(map(ord, pattern), replacement)))
                        self.controller.privmsg(msg.channel, '{}: {}'.format(msg.nick, body))
                    else:
                        # was invalid, return without adding this to their last messages
                        return

        # add it to the last messages dictionary
        last_messages[msg.nick] = body
