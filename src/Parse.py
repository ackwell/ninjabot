#This is something i just whipped up incase it was needed, feel free to delete

def parse_msg(s):
    """
    Breaks a message from an IRC server into its prefix, command, and arguments.
    """
    prefix = ''
    trailing = []
    
    if not s:
        raise Exception("Empty line.")
    
    if s[0] == ':':
        prefix, s = s[1:].split(' ', 1)
        
    if s.find(' :') != -1:
        s, trailing = s.split(' :', 1)
        args = s.split()
        args.append(trailing)
    else:
        args = s.split()
        
    command = args.pop(0)
    
    return {"pfx":prefix, "cmd":command, "args":args}

def get_nick(s):
    return s.split("!")[0]

def get_userhost(s):
    return s.split("!")[1]

def get_host(s):
    return s.split("@")[1]

def get_user(s):
    s = s.split("!")[1]
    return s.split("@")[0]