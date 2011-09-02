from Credentials import GOOGL
from urllib2 import Request, urlopen
from urllib import urlencode
import json

url="https://www.googleapis.com/urlshortener/v1/url"

def get_short(longUrl):
    data = {
            "longUrl":longUrl,
            "key":GOOGL["api_key"]
            }
    jdata = json.dumps(data)
    req = Request(url,jdata,{'content-type': 'application/json'})
    u = urlopen(req).read()
    return json.loads(u)["id"]

def get_long(shortUrl):
    args = {
            "shortUrl":shortUrl,
            "key":GOOGL["api_key"]
            }
    u = urlopen(url+"?"+urlencode(args)).read()
    return json.loads(u)["longUrl"]
