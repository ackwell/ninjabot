from urllib import urlopen, urlencode
from Credentials import PASTEBIN

import re

def write(string):
    url="http://pastebin.com/api/api_post.php"
    args={"api_paste_code": string,
              "api_option":"paste",
            "api_dev_key":PASTEBIN["api_dev_key"],
            "api_paste_expire_date":"1H"}
        
    u = urlopen(url,urlencode(args)).read()
    return u

def read(self, url):
    m = re.search(r'pastebin.com/([A-Za-z0-9]+$)', url)
    if m:
        url = "http://pastebin.com/raw.php?i=" + m.group(1)
        message = urlopen(url).read()
        return message