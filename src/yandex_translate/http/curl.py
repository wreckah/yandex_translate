# -*- coding: utf-8 -*-

import pycurl
from logging import getLogger
from urllib import urlencode
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
try:
    from ujson import loads
except ImportError:
    from json import loads


logger = getLogger(__name__)


def multi_query(url, chunks, lang, raise_errors=True, is_retry=False):
    curls = []
    res = []
    mc = pycurl.CurlMulti()
    for i in xrange(len(chunks)):
        res.append(StringIO())
        c = pycurl.Curl()
        c.setopt(pycurl.POST, 1)
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.HTTPHEADER, ['Connection: close'])
        c.setopt(pycurl.POSTFIELDS, urlencode({
            'text': chunks[i].encode('utf-8'),
            'lang': lang
        }))
        c.setopt(pycurl.WRITEFUNCTION, res[i].write)
        curls.append(c)
        mc.add_handle(c)

    i = 0
    cnt = len(chunks)
    while i < cnt:
        while 1:
            ret, num_handles = mc.perform()
            if ret != pycurl.E_CALL_MULTI_PERFORM:
                break
        while 1:
            num_q, ok_list, err_list = mc.info_read()
            for c in ok_list:
                mc.remove_handle(c)
                c.close()
            for c, errno, errmsg in err_list:
                mc.remove_handle(c)
                c.close()
            i += len(ok_list) + len(err_list)
            if num_q == 0:
                break
        # Currently no more I/O is pending, could do something in the meantime
        # (display a progress bar, etc.).
        # We just call select() to sleep until some more data is available.
        mc.select(0.1)

    mc.close()
    data = []
    for i in xrange(len(res)):
        res[i].seek(0)
        try:
            txt = res[i].read()
            data.append(loads(txt))
        except ValueError as e:
            if not is_retry:
                data.append(multi_query([chunks[i]], lang, raise_errors, True))
            else:
                if raise_errors:
                    raise
                logger.exception(e)
                data.append(chunks[i])
    return ''.join(data)
