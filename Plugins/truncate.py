# Plugin to truncate all output from ninjabot to stop flood/ensure important
# parts ie. URLs are displayed
import re

class Plugin:
    active = True

    def __init__(self, controller):
        self.controller = controller

        self.truncate_length = 400
        self.separator = '\002::\002'
        self.post_text = '... '

    def on_outgoing(self, msg):
        message_length = len(msg.body)
        if message_length <= self.truncate_length:
            return

        important_url = False
        urls = re.search(r'https?://[-A-Za-z0-9+&@#/%?=~_()|!:,.;]*[-A-Za-z0-9+&@#/%=~_()|]$', msg.body)
        if urls:
            important_url = True

        if important_url and self.separator in msg.body:
            message = msg.body.split(self.separator)
            content = message[-2]
            url = message[-1]
            max_content = self.truncate_length - len(message)*len(self.separator) - len(url) - len(self.post_text)
            for part in message[:-2]:
                max_content -= len(part)
            message[-2] = self.shorten_message(content, max_content)
            msg.body = self.separator.join(message)
        elif important_url:
            url = urls.group(0)
            content = msg.body[:message_length - len(url)]
            max_content = self.truncate_length - len(url) - len(self.post_text)
            content = self.shorten_message(content, max_content)
            msg.body = content + url
        else:
            max_content = self.truncate_length - len(self.post_text)
            msg.body = self.shorten_message(msg.body, max_content)
        return msg

    def shorten_message(self, content, max_content):
        is_space = content.rfind(' ', max_content - 50, max_content)
        if is_space != -1:
            content = content[:content.rfind(' ', max_content - 50, max_content)]
        else:
            content = content[:max_content]

        content += self.post_text
        return content



            

