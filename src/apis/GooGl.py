from Credentials import GOOGL
from urllib2 import Request, urlopen
from urllib import urlencode
import json

def get_short(longUrl):
    data = {
            "longUrl":longUrl,
            "key":GOOGL["api_key"]
            }
    jdata = json.dumps(data)
    req = Request(GOOGL["url"],jdata,{'content-type': 'application/json'})
    u = urlopen(req).read()
    return json.loads(u)["id"]

def get_long(shortUrl):
    args = {
            "shortUrl":shortUrl,
            "key":GOOGL["api_key"]
            }
    u = urlopen(GOOGL["url"]+"?"+urlencode(args)).read()
    return json.loads(u)["longUrl"]
