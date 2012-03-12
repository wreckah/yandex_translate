# -*- coding: utf-8 -*-

from urllib import urlencode
from urllib2 import urlopen, URLError
try:
    from ujson import loads
except ImportError:
    from json import loads


def multi_query(url, chunks, lang, raise_errors=True, is_retry=False):
    res = ''
    for i in xrange(len(chunks)):
        try:
            data = _query(url, chunks[i], lang)
        except (URLError, ValueError):
            try:
                data = _query(url, chunks[i], lang)
            except (URLError, ValueError):
                if raise_errors:
                    raise
                data = chunks[i]
        res += data
    return res

def _query(url, text, lang):
    return loads(urlopen(url, urlencode({
        'text': text.encode('utf-8'),
        'lang': lang,
    })).read())