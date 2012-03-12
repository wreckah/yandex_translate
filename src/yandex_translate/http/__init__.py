# -*- coding: utf-8 -*-

try:
    from pycurl import version
    from yandex_translate.http.curl import multi_query
except ImportError:
    from yandex_translate.http.simple import multi_query
