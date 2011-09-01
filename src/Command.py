import re
regex = re.compile(r"^(:(?P<prefix>[^ ]+) +)?(?P<command>[^ ]+)( *(?P<argument> .+))?")

PREFIX = "n: "


def on_public(string):
    p = _parse(string)

def on_private(string):
    p = _parse(string)

def _parse(string):
    parsed = regex.search(string)
    return parsed
    
    
def _execute_command():
    pass