from ApiSettings import GOOGL
from urllib2 import Request, urlopen
from urllib import urlencode
import json

def get_short(longUrl):
    """
    Given a standard URL, converts to a shortened URL
    Returns shortend URL
    """
    
    #Google only accetps it as a JSON header
    data = {
            "longUrl":longUrl,
            "key":GOOGL["api_key"]
            }
    jdata = json.dumps(data)
    req = Request(GOOGL["url"],jdata,{'content-type': 'application/json'})
    u = urlopen(req).read()
    return json.loads(u)["id"]

def get_long(shortUrl):
    """
    Converts a shortened URL back to the full URL
    Returns full URL
    """
    
    args = {
            "shortUrl":shortUrl,
            "key":GOOGL["api_key"]
            }
    u = urlopen(GOOGL["url"]+"?"+urlencode(args)).read()
    #I'll need to capture google's error messages and raise exceptins/NOTIFY nick etc
    return json.loads(u)["longUrl"]
