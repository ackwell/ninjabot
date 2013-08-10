from apis.BeautifulSoup import BeautifulSoup as bs, BeautifulStoneSoup as bss, Tag
from apis import googl
from apis import requests
import re
import urllib
import json

#I'm silencing all errors from webtools' autochecker, simply because there are so many that could pop up.
#/me is lazy

class Plugin:
	def __init__(self, controller, language):
		self.c = controller
		self.lang = language
		# Yeah, the bot is a chrome browser, ok? I'M NOT LYING, I SWEAR!
		self.useragent = 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.60 Safari/537.1'


	def sizeof_fmt(self, num):
		for x in ['bytes','KB','MB','GB','TB']:
			if num < 1024.0:
				return "%3.1f%s" % (num, x)
			num /= 1024.0


	def on_incoming(self, msg):
		if not msg.type == msg.CHANNEL: return
		if self.c.is_ignored(msg.nick): return

		try:
			urls = re.findall(r'https?://[-A-Za-z0-9+&@#/%?=~_()|!:,.;]*[-A-Za-z0-9+&@#/%=~_()|]', msg.body)
			for url in urls:
				if url.startswith('(') and url.endswith(')'):
					url = url[1:-1]

				filename = re.search(r'/([^/]+)/?$', url).groups(1)[0]
				#if '.' not in filename:
				#	url += ''

				req_headers = {}
				if self.lang:
					req_headers['Accept-Language'] = self.lang

				head = requests.head(url)

				if 'text/html' in head.headers['content-type']:
					req = requests.get(url,headers=req_headers)
					req = req.text
					r = re.search(r'(?s)<title>.*</title>', req)
					if not r: return
					title = bs(r.group(0), convertEntities=bs.HTML_ENTITIES).title.string.strip().replace('\n', '')
					message = 'Title: '+title
				else:
					content_type = head.headers['content-type']
					try: size = self.sizeof_fmt(int(head.headers['content-length']))
					except TypeError: size = "Unknown size"
					message = '%s: %s (%s)' % (filename, content_type, size)
				self.c.privmsg(msg.channel, message)
		except Exception as e:
			print e


	def trigger_w(self, msg):
		"Usage: w <search term>. Prints a short description of the corresponding wikipedia article."
		if len(msg.args) == 0:
			self.c.notice(msg.nick, "Please specify a search term")
			return

		params = {'action':'opensearch', 'format':'xml', 'limit':'2', 'search':' '.join(msg.args)}
		
		resp = bss(requests.post("http://en.wikipedia.org/w/api.php", data=params).text, convertEntities=bs.HTML_ENTITIES)

		if resp.textTag:
			index = 1 if 'may refer to:' in resp.descriptionTag.string else 0
			info = resp.findAll('description')[index].string.strip()
			url = resp.findAll('url')[index].string
			message = "\002Wikipedia ::\002 %s \002::\002 %s" % (info, googl.get_short(url,self.c.config))
			self.c.privmsg(msg.channel, message)
		else:
			self.c.privmsg(msg.channel, '%s: No articles were found.' % ' '.join(msg.args))
		

	def trigger_g(self, msg):
		"Usage: g <search term>. Prints title & short description of first google result."
		if len(msg.args) == 0:
			self.c.notice(msg.nick, "Please specify a search term")
			return

		url = "http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q=%s"%'+'.join(msg.args)
		headers = {'User-agent':self.useragent}
		entry = requests.get(url,headers=headers).text#bs(requests.get(url,params=params,headers=headers).text, convertEntities=bs.HTML_ENTITIES).find('div', 'vsc')
	
		#r = re.search(r'(?s)<div.*?class="vsc".*?>(.*?)</div>[^d]*?</li>', entry)
		#if not r:
		#	self.c.privmsg(msg.channel, '%s: No entries were found.'%' '.join(msg.args))
		#	return
		js=json.loads(entry)["responseData"]["results"][0];
		#if not al:
		#	return #because i have no idea what would cause this
		url = googl.get_short(js['url'], self.c.config)

		message = "\002\0032G\0034o\0038o\0032g\0033l\0034e\003 ::\002 %s \002::\002 %s \002::\002 %s" % (
			bs(js['titleNoFormatting'], convertEntities=bs.HTML_ENTITIES),
			re.sub("</?b>", "\002", js['content']),
			url)
		self.c.privmsg(msg.channel, message)


	def trigger_yt(self, msg):
		"Usage: yt <searchterm>. Prints title and link to first youtube result."
		if len(msg.args) == 0:
			self.c.notice(msg.nick, "Please specify a search term")
			return

		url = "https://gdata.youtube.com/feeds/api/videos"
		data = {'q':' '.join(msg.args), 'max-results':'1', 'v':'2', 'alt':'json'}
		url += '?' + urllib.urlencode(data)
		headers = {'User-agent':self.useragent}
		req = requests.get(url,headers=headers).text
		entry = json.loads(req)['feed']['entry']
		if len(entry) < 0:
			self.c.privmsg(msg.channel, '%s: No entries were found.'%' '.join(msg.args))
			return
		entry = entry[0]
		link = entry['link'][0]
		message = "\002You\0030,4Tube\003 ::\002 %s \002::\002 %s \002::\002 %s" % (
			entry['title']['$t'],
			entry['media$group']['media$description']['$t'],
			"http://youtu.be/"+entry['id']['$t'].split(':')[-1],)
		self.c.privmsg(msg.channel, message)


	def trigger_ud(self, msg):
		"Usage: ud <search term>. Prints first UrbanDictionary result."

		url = "http://www.urbandictionary.com/define.php"
		data = {'term':' '.join(msg.args)}
		soup = bs(requests.post(url,data=data).text, convertEntities=bs.HTML_ENTITIES)
		word = soup.find('td', 'word')
		if not word:
			self.c.privmsg(msg.channel, '%s: No entries were found.'%' '.join(msg.args))
			return

		word = self.tag2string(word).strip()
		defi = self.tag2string(soup.find('div', 'definition')).split('<br')[0]
		self.c.privmsg(msg.channel, '%s: %s'%(word,defi,))

	def trigger_tx(self, msg):
		"Usage: tx <expression>. Prints a link to a graphical representation of the supplied LaTeX expression."

		url = "http://www.texify.com/$%s$" % urllib.quote(' '.join(msg.args))
		self.c.privmsg(msg.channel, 'LaTeX :: %s' % googl.get_short(url, self.c.config))

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


