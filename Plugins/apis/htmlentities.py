
import re
from htmlentitydefs import entitydefs as ENTITIES

fix_charcodes = lambda code: "\u" . hex(int(code.groups()[0]))
fix_entities  = lambda name: ENTITIES[name.groups()[0]] if name.groups()[0] in ENTITIES else u"\u000304" + name.groups()[0] + u"\u000f" # red!


def clear_entities(text):
	#print u"Entity-freeing %s"%unicode(text)
	text = re.sub("&amp;", "&", text);
	text = re.sub("&(\w+?);", fix_entities, text);
	text = re.sub("&#(\d\d\d);", fix_charcodes, text);
	return text

	
