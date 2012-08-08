from urllib2 import Request, urlopen
from urllib import urlencode
import json

def get_short(longUrl, config):
    """
    Given a standard URL, converts to a shortened URL
    Returns shortend URL
    """
    
    #Google only accetps it as a JSON header
    data = {
            "longUrl":longUrl,
            "key":config[googl]["api-key"]
            }
    jdata = json.dumps(data)
    req = Request("https://www.googleapis.com/urlshortener/v1/url",jdata,{'content-type': 'application/json'})
    u = urlopen(req).read()
    return json.loads(u)["id"]

def get_long(shortUrl, config):
    """
    Converts a shortened URL back to the full URL
    Returns full URL
    """
    
    args = {
            "shortUrl":shortUrl,
            "key":config['googl']["api-key"]
            }
    u = urlopen("https://www.googleapis.com/urlshortener/v1/url?"+urlencode(args)).read()
    #I'll need to capture google's error messages and raise exceptins/NOTIFY nick etc
    return json.loads(u)["longUrl"]
