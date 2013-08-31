from apis import googl
import xml.etree.ElementTree as ElementTree
import requests
import urllib

class Plugin:
    active = True

    def __init__(self, controller, appid):
        self.controller = controller
        self.appid = appid

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
                     'input' : ' '.join(msg.args),
                     'format': 'plaintext'}

        # Perform the query and form XML Tree
        response = self.session.post(self.queryurl, data=querydata)
        tree = ElementTree.XML(response.text.encode('utf-8'))

        # Check for error
        if tree.get('error') == 'true':
            self.controller.privmsg(msg.channel, '{} Error.'.format(self.prefix))
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
                querydata['input'] = try_next
                response = self.session.post(self.queryurl, data=querydata)
                tree = ElementTree.XML(response.text.encode('utf-8'))
                if tree.get('error') == 'true':
                    self.controller.privmsg(msg.channel, '{} Error.'.format(self.prefix))
                    return
                # When a proper result has been obtained:
                if tree.get('success') == 'true':
                    # Set the interpretation and continue on
                    interpretation = try_next
                    break
            else:
                # There were no suitable alternatives
                self.controller.privmsg(msg.channel, '{} Could not interpret input.'.format(self.prefix))
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
                            result = result.replace('\n',' ')
                        if len(result) > 100:
                            result = result[:result.find(' ',100)] + '...'
                        if len(result) > 200:
                            result = result[:200] + '...'
                        #print '--',result
                # Get the title for output and add to results
                podtitle = pod.get('title')
                if result == '' and subpod_count > 1:
                    result = pod.iterfind('subpod').next().findtext('plaintext')
                    result += '. ' + str(int(subpod_count) - 1) + ' other forms'
                results.append((podtitle, result))
            # If WA interprets the query differently, use it
            if pod.get('title') == 'Input interpretation':
                for subpod in pod.iterfind('subpod'):
                    interpretation = subpod.findtext('plaintext')
                    #print 'int -', interpretation

        if '\n' in interpretation:
            interpretation = interpretation.replace('\n',' ')
        if len(interpretation) > 100:
            interpretation = interpretation[:interpretation.find(' ',100)] + '...'
        if len(interpretation) > 200:
            interpretation = interpretation[:200] + '...'
        # Notify of use of alternate interpretation
        if interpretation != '':
            self.controller.privmsg(msg.channel, '{} Interpreting as `{}\'.'.format(self.prefix, interpretation))

        # Add all results to messages and send at once
        messages = []
        for result in results:
            messages.append('{} {} \002::\002 {}'.format(self.prefix, result[0], result[1]))
        if not results:
            messages.append('{} No primary results.'.format(self.prefix))

        # Add a goo.gl url to last result
        messages[-1] += ' \002::\002 '
        messages[-1] += googl.get_short('http://www.wolframalpha.com/input/?i=%s' % urllib.quote_plus(' '.join(msg.args).encode('utf-8')), self.controller.config)

        for message in messages:
            self.controller.privmsg(msg.channel, message)
