"""
Watches incoming channel messages for URLs, and posts information on those it finds.
"""

import re
import requests
from bs4 import BeautifulSoup
from requests.utils import get_encodings_from_content


class Plugin(object):
	def load(self, bot, config):
		self.bot = bot
		self.utils = self.bot.request_api('web.utils')

		# Matches against standard-compliant URLs in a string
		self.url_re = re.compile(r'\(*?https?://[-A-Za-z0-9+&@#/%?=~_()|!:,.;]*[-A-Za-z0-9+&@#/%=~_()|]')

	def on_incoming(self, msg):
		if not msg.type == msg.CHANNEL:
			return

		# Catching all exceptions without alerting, as there is just so much crap that can go wrong with web stuff. Also, I'm lazy.
		try:
			urls = self.url_re.findall(msg.body)
			for url in urls:
				# Catch edge case where url is in brackets
				while url.startswith('(') and url.endswith(')'):
					url = url[1:-1]

				head = requests.head(url, allow_redirects=True)
				# work on the URL we were redirected to, if any
				url = head.url

				message = ""
				content_type = head.headers['content-type']

				# HTML websites
				if 'text/html' in content_type:
					# Set up any required request headers
					req_headers = {}
					# TODO: Accept-Language header from config

					req = requests.get(url, headers=req_headers, timeout=5)

					if 'charset' not in content_type:
						# requests only looks at headers to detect the encoding, we must find the charset ourselves
						# we can't use req.content because regex doesn't work on bytestrings apparently
						encodings = get_encodings_from_content(req.text)
						if encodings:
							req.encoding = encodings[0]

					soup = BeautifulSoup(req.text)

					# Look for the <title> tag or an <h1>, whichever is first
					title = soup.find(['title', 'h1'])
					if title is None:
						return
					title = self.utils.tag_to_string(title)
					title = ' '.join(title.split())
					message = "Title: " + title

				# Other resources
				else:
					content_length = head.headers.get('content-length', '')
					if content_length.isdigit():
						size = self.sizeof_fmt(int(content_length))
					else:
						size = "Unknown size"

					# Searches for the last segment of the URL (the filename)
					filename = re.search(r'/([^/]+)/?$', url).groups(1)[0]

					message = "{}: {} ({})".format(filename, content_type, size)

				self.bot.privmsg(msg.channel, message)

		except Exception as exception:
			print("Link Info Exception!")
			print(type(exception), exception)

	def sizeof_fmt(self, num):
		for unit in ["bytes", "KB", "MB", "GB", "TB"]:
			if num < 1024.0:
				return "{:3.1f}{}".format(num, unit)
			num /= 1024.0
