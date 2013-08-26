#Wikipedia plugin by peterarenot
from apis import wikipedia

class Plugin:
	def __init__(self, bot, config):
		self.bot = bot
		self.config = config

	def on_incoming(self, msg):
		if 'wikipedia' in msg.body.lower():
			self.bot.notice(msg.nick, "Did you know I can search Wikipedia? Use '%swiki <query>'"%self.bot.command_prefix)
		return msg

	def trigger_wiki(self, msg):
		"Usage: wiki <query> | Search wikipedia for query"
		# Check that something is being searched
		if len(msg.args) == 0:
			self.bot.notice(msg.nick, "Play nice! Enter a query as well!")
			return

		# Make query string
		queryString = " ".join(msg.args)

		# Ask the source of all knowledege
		try:
			result = wikipedia.summary(queryString, sentences=2)
		except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError, wikipedia.exceptions.RedirectError):
			self.bot.notice(msg.nick, "Well, what you have done is broken it. This is why we can't have nice things. Try again with a better search.")
			return

		self.bot.notice(msg.channel, result)

	def trigger_randomwiki(self, msg):
		"Get the summary of a random wikipedia article"
		try:
			result = wikipedia.summary(wikipedia.random(pages=1), sentences=2)
		except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError, wikipedia.exceptions.RedirectError):
			self.bot.notice(msg.nick, "Well, what you have done is broken it. This is why we can't have nice things. Try again with a better search.")
			return

		self.bot.notice(msg.channel, result)