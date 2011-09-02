from urllib import urlopen, urlencode
from ApiSettings import PASTEBIN

import re

def write(string):
    """
    Write <string> to a new Pastebin
    Returns pastebin URL
    """
    
    url=PASTEBIN["send_url"]
    args={"api_paste_code": string,
          "api_option":"paste",
          "api_dev_key":PASTEBIN["api_key"],
          "api_paste_expire_date":"1H"}
        
    u = urlopen(url,urlencode(args)).read()
    return u

def read(self, url):
    """
    Read content of given pastebin URL
    Returns string of content
    """
    
    m = re.search(r'pastebin.com/([A-Za-z0-9]+$)', url)
    if m:
        url = PASTEBIN["get_url"] + m.group(1)
        message = urlopen(url).read()
        return message