from urllib.request import urlopen
from urllib.parse import urlencode
import re, json

def write(string, private=True, expire=3600):
    """
    Write <string> to a new kdepaste
    Returns kdepaste URL or error message
    """

    url='http://paste.kde.org/'
    args={'paste_data': string,
          'paste_lang': 'text',
          'api_submit':'true',
          'mode': 'json',

          'paste_private': 'yes' if private else 'no',
          'paste_expire': expire
          }
    post_data = urlencode(args).encode('utf-8')

    u = urlopen(url, post_data).read().decode('utf-8')
    j = json.loads(u)['result']
    if 'error' in j.keys():
        return j['error']
    o = 'http://paste.kde.org/%s/%s'%(j['id'], j['hash'] if private else '')
    return o

#removed the read() function, as it's a lot easier with KDE paste so there's no point really.