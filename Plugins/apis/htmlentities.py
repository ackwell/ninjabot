import re
from htmlentitydefs import entitydefs as ENTITIES

def fix_charcodes(code):
    return unichr(int(code.groups()[0]))

def fix_entities(name):
    return ENTITIES.get(name.groups()[0], u"\u000304" + name.groups()[0] + u"\u000f")

def clear_entities(text):
    #print u"Entity-freeing %s"%unicode(text)
    text = unicode(text)
    text = re.sub(r'&(\w+);',  fix_entities,  text);
    text = re.sub(r'&#(\d+);', fix_charcodes, text);
    return text

    
