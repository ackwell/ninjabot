# Git API
# a Python wrapper around the command line tools

# N.B. this has been written 100% with *nix in mind, don't bother trying to use it in windows
# ... yes, i'm talking to you, saxon >.>

# >george's face when it runs seamlessly on windows
# >george's face when he has no face

import subprocess

class Git(object):
    def __init__(self, repo):
        self.repo = repo

    def pull(self):
        output = subprocess.check_output(['git', '--git-dir', self.repo, 'pull'])
        return output.strip()
