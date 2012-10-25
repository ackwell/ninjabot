import json
import requests

def get_short(longUrl, config):
    """
    Given a standard URL, converts to a shortened URL
    Returns shortend URL
    """
    
    #Google only accetps it as a JSON header
    headers = {'content-type': 'application/json'}

    data = {
            'longUrl': longUrl,
            'key': config['apis']['googl']
            }

    req = requests.post('https://www.googleapis.com/urlshortener/v1/url', data=json.dumps(data), headers=headers)
    #print req.json
    return req.json['id']

def get_long(shortUrl, config):
    """
    Converts a shortened URL back to the full URL
    Returns full URL
    """

    data = {
            "shortUrl":shortUrl,
            "key":config['apis']['googl']
            }
    req = requests.get("https://www.googleapis.com/urlshortener/v1/url", params=data)
    #I'll need to capture google's error messages and raise exceptins/NOTIFY nick etc
    return req.json["longUrl"]
