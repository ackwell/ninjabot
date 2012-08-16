from apis import googl
from apis import requests
import xml.etree.ElementTree as ElementTree
import urllib

class Plugin:
    active = True

    def __init__(self, controller):
        self.controller = controller
        self.appid = self.controller.config['wolfram']['appid']

        self.queryurl = 'http://api.wolframalpha.com/v2/query'
        self.session = requests.session()

        self.prefix = '\002\0034W\0038A\003 ::\002'

    def trigger_wa(self, msg):
        "Usage: wa <query>. Prints the top result from WolframAlpha."
        if len(msg.args) == 0:
            self.controller.notice(msg.nick, "Please specify a query")
            return

        # Set up the required data for the query
        querydata = {'appid' : self.appid,
                     'input' :' '.join(msg.args),
                     'format':'plaintext'}

        # Perform the query and form XML Tree
        response = self.session.post(self.queryurl, data=querydata)
        tree = ElementTree.XML(response.text.encode('utf-8'))

        # Check for error
        if tree.get('error') == 'true':
            self.controller.privmsg(msg.channel, '%s Error.' % self.prefix)
            return

        # Interpretation may or may not differ from query
        interpretation = ''

        # Check for didyoumeans, when the query is derp and requires a different interpretation
        if tree.get('success') == 'false':
            didyoumeans_list = []
            # Get alternatives
            for didyoumeans in tree.iterfind('didyoumeans'):
                for didyoumean in didyoumeans.iterfind('didyoumean'):
                    didyoumeans_list.append(didyoumean.text)
            # Try alternatives
            for try_next in didyoumeans_list:
                querydata = {'appid' : self.appid,
                             'input' : try_next,
                             'format':'plaintext'}
                response = self.session.post(self.queryurl, data=querydata)
                tree = ElementTree.XML(response.text.encode('utf-8'))
                if tree.get('error') == 'true':
                    self.controller.privmsg(msg.channel, '%s Error.' % self.prefix)
                    return
                # When a proper result has been obtained:
                if tree.get('success') == 'true':
                    # Set the interpretation and continue on
                    interpretation = try_next
                    break
            else:
                # There were no suitable alternatives
                self.controller.privmsg(msg.channel, '%s Could not interpret input.' % self.prefix)
                return

        # Can be more than one result so store a list
        results = []

        # Iterate through all 'pod' elements
        for pod in tree.iterfind('pod'):
            #print pod.get('title')
            if pod.get('primary') == 'true' or pod.get('title') == 'Result':
                # If it is a primary pod (good result) check through subpods
                result = ''
                subpod_count = pod.get('numsubpods')
                for subpod in pod.iterfind('subpod'):
                    # Only take primary subpods/lone subpods
                    if subpod.get('primary') == 'true' or subpod_count == '1':
                        result = subpod.findtext('plaintext')
                        if '\n' in result:
                            # Adds '...' if result is multiline
                            result = result.replace('\n',' ')#result.split('\n')[0] + '...'
                        if len(result) > 100:
                            result = result[:result.find(' ',100)] + '...'
                        #print '--',result
                # Get the title for output and add to results
                if result == '' and subpod_count > 1:
                    podtitle = 'Results'
                    result = 'Too many results'
                else:
                    podtitle = pod.get('title')
                results.append((podtitle, result))
            # If WA interprets the query differently, use it
            if pod.get('title') == 'Input interpretation':
                for subpod in pod.iterfind('subpod'):
                    interpretation = subpod.findtext('plaintext')
                    #print 'int -', interpretation

        # Notify of use of alternate interpretation
        if interpretation != '':
            self.controller.privmsg(msg.channel, '%s Interpreting as `%s`.' % (self.prefix, interpretation))

        # Add all results to messages and send at once
        messages = []
        for result in results:
            messages.append('%s %s \002::\002 %s' % (self.prefix, result[0], result[1]))
        if not results:
            messages.append('%s No primary results.' % self.prefix)

        # Add a goo.gl url to last result
        messages[-1] += ' \002::\002 '
        messages[-1] += googl.get_short('http://www.wolframalpha.com/input/?i=%s' % urllib.quote_plus(' '.join(msg.args)), self.controller.config)

        for message in messages:
            self.controller.privmsg(msg.channel, message)
