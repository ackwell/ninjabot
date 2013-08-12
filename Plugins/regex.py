# Regex Plugin for ninjabot

from collections import defaultdict, deque
import re

BACKLOG = 3 # keep this many past messages saved for each user

last_messages = defaultdict(deque)

class Plugin:
    def __init__(self, controller, config):
        self.controller = controller

    def on_incoming(self, msg):
        nick = msg.nick

        # Ignore those who have been ignored...
        if self.controller.is_ignored(nick): return

        if msg.type == msg.CHANNEL:
            # check if the message matches the s/blah/blah/ syntax
            ## regex could have been used for this, but factoring in those escaped forward slashes
            ## would have been more trouble than it was worth...
            # Challenge accepted, spake. --auscompgeek
            body = msg.body
            matches = re.match(r'''(?x)     # verbose mode
                        ^(s)(/)             # starts with s, then / (our separator)
                        ((?: # capture pattern
                            (?:\\\2)*       # any number of escaped separators
                            [^/]*           # any number of non-seps
                            (?:(?:\\\2)+[^/])*
                        )*)  # ...as many times as possible, end capture pattern
                        \2                  # separator
                        ((?:
                            (?:\\\2)*
                            [^/]*
                            (?:(?:\\\2)+[^/])*
                        )*)
                        (?:\2([g0-9])?)?$   # end with optional separator with optional flags
                    ''', body)

            if matches:
                groups = matches.groups()

                # did they have a last message?
                if msg.nick in last_messages:
                    their_messages = last_messages[nick]
                    mode, sep, pattern, replacement, flags = [s.replace('\\'+groups[1], groups[1]) if s else '' for s in groups]

                    if mode == 's':  # string replace mode
                        # escape backslashes
                        replacement = replacement.replace('\\', '\\\\')

                        # scan for a matching message in their last messages
                        for message in their_messages:
                            try: # will treat the regex as a normal message if an error occurs, i.e. invalid syntax
                                if re.search(pattern, message):
                                    if 'g' in flags:
                                        body = re.sub(pattern, replacement, message)
                                    elif flags.isdigit():
                                        matches = re.findall(pattern, message)
                                        if len(matches) >= int(flags):
                                            span = matches[int(flags)-1].span()
                                            body = message[:span[0]] + replacement + message[span[1]:]
                                        else:
                                            return
                                    else:
                                        body = re.sub(pattern, replacement, message, 1)

                                    # put backslashes back in
                                    body = body.replace('\\\\', '\\')

                                    # send it
                                    if body == "":
                                        self.controller.privmsg(msg.channel, nick + ' said nothing')
                                    else:
                                        self.controller.privmsg(msg.channel, '{} meant to say: {}'.format(nick, body))

                                    break
                            except:
                                pass
                        else:
                            # match wasn't found
                            # return without adding this to their last messages
                            return

            # add it to the last messages dictionary
            their_messages = last_messages[nick]
            their_messages.appendleft(body)
            if len(their_messages) > BACKLOG:
                their_messages.pop()
