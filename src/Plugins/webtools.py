from apis.BeautifulSoup import BeautifulSoup as bs, BeautifulStoneSoup as bss, Tag
from urlparse import urlparse
import re
import urllib, urllib2
import httplib

class Plugin:
	def __init__(self, controller):
		self.c = controller

	def sizeof_fmt(self, num):
		for x in ['bytes','KB','MB','GB','TB']:
			if num < 1024.0:
				return "%3.1f%s" % (num, x)
			num /= 1024.0

	def on_incoming(self, msg):
		if not msg.type == 1: return

		urls = re.findall(r'\(?\bhttps?://[-A-Za-z0-9+&@#/%?=~_()|!:,.;]*[-A-Za-z0-9+&@#/%=~_()|]', msg.body)
		for url in urls:
			if url.startswith('(') and url.endswith(')'):
				url = url[1:-1]

			o = urlparse(url)
			conn = httplib.HTTPConnection(o.netloc)
			conn.request("HEAD", o.path)
			head = conn.getresponse()

			if 'text/html' in head.getheader('content-type'):
				message = 'Title: '+bs(urllib.urlopen(url), convertEntities=bs.HTML_ENTITIES).title.string.strip().replace('\n', '')
			else:
				message = '%s: %s (%s)' % (re.search(r'/([^/]+)$', url).groups(1)[0], head.getheader('content-type'), self.sizeof_fmt(int(head.getheader('content-length'))))
			self.c.privmsg(msg.channel, message)

	def trigger_w(self, msg):
		"Usage: w <search term>. Prints a short description of the corresponding wikipedia article."
		if len(msg.args) == 0:
			self.c.notice(msg.nick, "Please specify a search term")
			return

		params = {'action':'opensearch', 'format':'xml', 'limit':'2', 'search':urllib.quote_plus(' '.join(msg.args))}
		
		resp = bss(urllib.urlopen("http://en.wikipedia.org/w/api.php?%s" % urllib.urlencode(params)), convertEntities=bs.HTML_ENTITIES)

		if resp.textTag:
			index = 1 if 'may refer to:' in resp.descriptionTag.string else 0
			self.c.privmsg(msg.channel, resp.findAll('description')[index].string)
		else:
			self.c.privmsg(msg.channel, 'No articles were found.')
		

	def trigger_g(self, msg):
		"Usage: g <search term>. Prints title & short description of first google result."
		if len(msg.args) == 0:
			self.c.notice(msg.nick, "Please specify a search term")
			return

		url = "https://www.google.com.au/search?q=%s" % (urllib.quote_plus(' '.join(msg.args)),)
		req = urllib2.Request(url, None, {'User-agent':'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.60 Safari/537.1'})
		entry = bs(urllib2.urlopen(req), convertEntities=bs.HTML_ENTITIES).find('div', 'vsc')

		r = r'<.+?>'
		message = "%s: %s" % (
			re.sub(r,'',self.tag2string(entry.find('a','l'))),
			re.sub(r,'',self.tag2string(entry.find('span','st'))),)
		self.c.privmsg(msg.channel, message)


	def trigger_ud(self, msg):
		"Usage: ud <search term>. Prints first UrbanDictionary result."

		url = "http://www.urbandictionary.com/define.php?term="+urllib.quote_plus(' '.join(msg.args))
		soup = bs(urllib2.urlopen(url), convertEntities=bs.HTML_ENTITIES)
		word = soup.find('td', 'word')
		if not word:
			self.c.privmsg(msg.channel, 'No entries were found.')
			return

		word = self.tag2string(word).strip()
		defi = self.tag2string(soup.find('div', 'definition')).split('<br')[0]
		self.c.privmsg(msg.channel, '%s: %s'%(word,defi,))


	def tag2string(self, tag):
		if tag.string == None:
			ret = ''
			for item in tag.contents:
				if type(item) is Tag:
					ret += self.tag2string(item)
				else:
					ret += item
			return ret
		else:
			return tag.string



