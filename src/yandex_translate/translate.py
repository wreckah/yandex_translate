# -*- coding: utf-8 -*-

import re
import urllib
try:
    from ujson import loads
except ImportError:
    from json import loads
from yandex_translate.http import multi_query


class UnknownTranslateDirectionError(ValueError):
    pass


class Translate(object):

    _ESCAPE_MARKER = '======='
    _escaped_patterns = None
    CHUNK_SIZE = 2000
    API_URL = 'http://translate.yandex.ru/tr.json/'
    TRANSLATE_URL = API_URL + 'translate'
    DIRECTION_URL = API_URL + 'getLangs'
    directions = None
    raise_errors = True


    def __init__(self, raise_errors=True):
        self._escaped_patterns = [
            re.compile(r'<[^>]+>'), # escape translation of HTML tags
        ]
        self.raise_errors = raise_errors

    def translate(self, text, direction='en-ru', escape=True):
        if self.directions is None:
            self.directions = self.get_directions()
        if direction not in self.directions:
            raise UnknownTranslateDirectionError(direction)
        if escape:
            text, replaces = self._escape(text)
        chunks = self._split_to_chunks(text)
        text = multi_query(self.TRANSLATE_URL, chunks, direction)
        if escape:
            text = self._unescape(text, replaces)
        return text

    def get_directions(self):
        return loads(
            urllib.urlopen(self.DIRECTION_URL).read()
        )['dirs']

    def _split_to_chunks(self, text):
        chunks = []
        while len(text) > self.CHUNK_SIZE:
            chunk = text[:self.CHUNK_SIZE]
            pos = chunk.rfind('. ')
            if pos > 0:
                chunks.append(chunk[:pos+2])
                text = chunk[pos+2:] + text[self.CHUNK_SIZE:]
                continue
            pos = chunk.rfind(' ')
            if pos > 0:
                chunks.append(chunk[:pos+1])
                text = chunk[pos+1:] + text[self.CHUNK_SIZE:]
                continue
            chunks.append(chunk)
            text = text[self.CHUNK_SIZE:]
        chunks.append(text)
        return chunks

    def append_escape_pattern(self, rgx):
        self._add_escape_pattern(self, rgx, True)

    def prepend_escape_pattern(self, rgx):
        self._add_escape_pattern(self, rgx, False)

    def _add_escape_pattern(self, rgx, is_append):
        if isinstance(rgx, (list, tuple)):
            for item in reversed(rgx):
                if is_append:
                    self._escaped_patterns.append(self._pattern(item))
                else:
                    self._escaped_patterns.insert(0, self._pattern(item))
        else:
            if is_append:
                self._escaped_patterns.append(self._pattern(rgx))
            else:
                self._escaped_patterns.insert(0, self._pattern(rgx))

    @staticmethod
    def _pattern(str_or_rgx):
        if isinstance(str_or_rgx, basestring):
            return re.compile(str_or_rgx)
        else:
            return str_or_rgx

    def _escape(self, text):
        replaces = []
        marker = self._ESCAPE_MARKER
        text = text.replace(marker, marker[0]+' '+marker[1:])
        for rgx in self._escaped_patterns:
            diff = 0
            _replaces = []
            marker_len = len(marker)
            for match in rgx.finditer(text):
                _replaces.append(match.group(0))
                text = text[:match.start()-diff] + marker + text[match.end()-diff:]
                diff += len(match.group(0)) - marker_len
            replaces.append({'marker': marker, 'replaces': _replaces})
            marker += '<>'
        return text, replaces
    
    def _unescape(self, text, replaces):
        for _replaces in reversed(replaces):
            marker = _replaces['marker']
            marker_len = len(marker)
            for replace in _replaces['replaces']:
                pos = text.find(marker)
                if pos != -1:
                    text = text[:pos] + replace + text[pos+marker_len:]
        return text
