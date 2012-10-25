# tr Plugin for ninjabot

from string import maketrans
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
                    ^(?:y|tr)/          # starts with y/ or tr/
                    (
                        (?:\\/)*        # any number of escaped /
                        [^/]+           # at least 1 non-/
                        (?:\\/[^/]*)*   # an escaped / and any number of non-/, repeatedly
                    )
                    /                   # literal /
                    ((?:\\/)*[^/]+(?:\\/[^/]*)*) # the above again
                    /?$                 # end with optional /
                ''', body)
        if matches != None:
            groups = matches.groups()
            # did they have a last message?
            if msg.nick in last_messages:
                last_message = last_messages[msg.nick]
                if len(groups) == 2:
                    pattern, replacement = map(lambda s: s.replace('\\/', '/'), groups)
                    if len(pattern) == len(replacement):
                        body = last_message.translate(dict(zip(map(ord, pattern), replacement)))
                        self.controller.privmsg(msg.channel, '%s: %s' % (msg.nick, body))
                    else:
                        # was invalid, return without adding this to their last messages
                        return

        # add it to the last messages dictionary
        last_messages[msg.nick] = body
