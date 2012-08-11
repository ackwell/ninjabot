# Git API
# a Python wrapper around the command line tools

# N.B. this has been written 100% with *nix in mind, don't bother trying to use it in windows
# ... yes, i'm talking to you, saxon >.>

import subprocess

class Git(object):
    def __init__(self):
        pass

    def pull(self):
        output = subprocess.check_output(['git', 'pull'])
        return output.strip()
