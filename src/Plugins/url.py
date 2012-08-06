from BeautifulSoup import BeautifulSoup as bs
from urlparse import urlparse
import re
import urllib
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
				message = 'Title: '+bs(urllib.urlopen(url)).title.string.strip().replace('\n', '')
			else:
				message = '%s: %s (%s)' % (re.search(r'/([^/]+)$', url).groups(1)[0], head.getheader('content-type'), self.sizeof_fmt(int(head.getheader('content-length'))))

			self.c.privmsg(msg.channel, message)


