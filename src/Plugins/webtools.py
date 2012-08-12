from apis.BeautifulSoup import BeautifulSoup as bs, BeautifulStoneSoup as bss, Tag
from apis import googl
from urlparse import urlparse
import re
import urllib, urllib2
import httplib

#I'm silencing all errors from webtools' autochecker, simply because there are so many that could pop up.
#/me is lazy

class Plugin:
	def __init__(self, controller):
		self.c = controller
		self.useragent = 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.60 Safari/537.1'


	def sizeof_fmt(self, num):
		for x in ['bytes','KB','MB','GB','TB']:
			if num < 1024.0:
				return "%3.1f%s" % (num, x)
			num /= 1024.0


	def on_incoming(self, msg):
		if not msg.type == msg.CHANNEL: return

		try:
			urls = re.findall(r'\(?\bhttps?://[-A-Za-z0-9+&@#/%?=~_()|!:,.;]*[-A-Za-z0-9+&@#/%=~_()|]', msg.body)
			for url in urls:
				if url.startswith('(') and url.endswith(')'):
					url = url[1:-1]

				filename = re.search(r'/([^/]+)/?$', url).groups(1)[0]
				if '.' not in filename:
					url += ''

				o = urlparse(url)
				conn = httplib.HTTPConnection(o.netloc)
				conn.request("HEAD", o.path)
				head = conn.getresponse()

				if 'text/html' in head.getheader('content-type'):
					message = 'Title: '+bs(urllib.urlopen(url), convertEntities=bs.HTML_ENTITIES).title.string.strip().replace('\n', '')
				else:
					content_type = head.getheader('content-type')
					try: size = self.sizeof_fmt(int(head.getheader('content-length')))
					except TypeError: size = "Unknown size"
					message = '%s: %s (%s)' % (filename, content_type, size)
				self.c.privmsg(msg.channel, message)
		except:
			pass


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
			self.c.privmsg(msg.channel, '%s: No articles were found.'%' '.join(msg.args))
		

	def trigger_g(self, msg):
		"Usage: g <search term>. Prints title & short description of first google result."
		if len(msg.args) == 0:
			self.c.notice(msg.nick, "Please specify a search term")
			return

		url = "https://www.google.com.au/search?q=%s" % (urllib.quote_plus(' '.join(msg.args)),)
		req = urllib2.Request(url, None, {'User-agent':self.useragent})
		entry = bs(urllib2.urlopen(req), convertEntities=bs.HTML_ENTITIES).find('div', 'vsc')

		if not entry:
			self.c.privmsg(msg.channel, '%s: No entries were found.'%' '.join(msg.args))
			return

		url = googl.get_short(entry.find('a','l')['href'], self.c.config)
		message = "\002\0032G\0034o\0038o\0032g\0033l\0034e\003 ::\002 %s \002::\002 %s \002::\002 %s" % (
			self.tag2string(entry.find('a','l')),
			self.tag2string(entry.find('span','st')),
			url,)
		self.c.privmsg(msg.channel, message)


	def trigger_yt(self, msg):
		"Usage: yt <searchterm>. Prints title and link to first youtube result."
		if len(msg.args) == 0:
			self.c.notice(msg.nick, "Please specify a search term")
			return

		url = "http://www.youtube.com/results?search_query=%s" % (urllib.quote_plus(' '.join(msg.args)),)
		req = urllib2.Request(url, None, {'User-agent':self.useragent})
		entry = bs(urllib2.urlopen(req), convertEntities=bs.HTML_ENTITIES).find('div', 'yt-lockup-content')

		if not entry:
			self.c.privmsg(msg.channel, '%s: No entries were found.'%' '.join(msg.args))
			return

		message = "\002You\0030,4Tube\003 ::\002 %s \002::\002 %s \002::\002 %s" % (
			entry.find('a', 'yt-uix-contextlink').string,
			self.tag2string(entry.find('p', 'description')),
			"www.youtube.com"+entry.find('a', 'yt-uix-contextlink')['href'],)
		self.c.privmsg(msg.channel, message)


	def trigger_ud(self, msg):
		"Usage: ud <search term>. Prints first UrbanDictionary result."

		url = "http://www.urbandictionary.com/define.php?term="+urllib.quote_plus(' '.join(msg.args))
		soup = bs(urllib2.urlopen(url), convertEntities=bs.HTML_ENTITIES)
		word = soup.find('td', 'word')
		if not word:
			self.c.privmsg(msg.channel, '%s: No entries were found.'%' '.join(msg.args))
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


