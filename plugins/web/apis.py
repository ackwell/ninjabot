
"""
plugins/web APIs
For obvious reasons, a lot of the web tool plugins share code, this is
just a central API file to keep that in.
"""

from bs4 import BeautifulSoup, Tag


class WebAPI:
	def tag_to_string(self, tag, keep_bold=False):
		if tag.string is None:
			result = ''
			for item in tag.contents:
				if isinstance(item, Tag):
					if keep_bold and item.name == 'b':
						result += '\002'
						result += self.tag_to_string(item)
						result += '\002'
					else:
						result += self.tag_to_string(item)
				else:
					result += item
			return result
		else:
			return tag.string

	def cull_html(self, text):
		soup = BeautifulSoup(text)
		result = self.tag_to_string(soup, keep_bold=True)
		# Doing this to strip out any newlines.
		return ' '.join(result.split())


APIS = {
	'web.utils': WebAPI()
}
