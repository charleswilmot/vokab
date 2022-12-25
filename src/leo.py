#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# Query the dictionary http://dict.leo.org/ from within Python.
# This is based on an equivalent script for German/English by:
#
# Copyright (C) 2015 Ian Denhardt <ian@zenhack.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#------------------------------------------------------------------------------
# Usage:
#------------------------------------------------------------------------------
# import LeoAccess as leo
# ret = leo.search("some string")
#------------------------------------------------------------------------------
# 'ret' will be {} if nothing found or any error, or contain a dictionary with a
# variable number of 'section_names' (see below) as keys.
# The value of each key is a list of sub-dictionaries of word pairs
# {"sl": "source", "de": "german"}.
# When required, the dictionary 'sn_de' can be used to translate section_names
# into German.
#------------------------------------------------------------------------------
# Dependencies:
# requests, lxml, io
#------------------------------------------------------------------------------
import requests
from lxml import etree
from io import StringIO
import logging


logger = logging.getLogger(__name__)


#==============================================================================
# Constants
#==============================================================================
sl = 'es'                    # default source language (Spanish - Español)
# Currently (Feb 2016), the following languages are available in LEO:
# English (en), tested, 800 k-entries
# French (fr), tested, 250 k-entries
# Spanish (es), tested, 200 k-entries
# Italian (it), tested, 180 k-entries
# Chinese (ch), tested, 186 k-entries
# Russian (ru), tested, 272 k-entries
# Portuguese (pt), tested, 82 k-entries
# Polish (pl), tested, 59 k-entries
tl = 'de'                    # target language (German). Actually a constant:
                             # LEO is a German company
uri = 'http://dict.leo.org/%s%s/' # LEO uri
section_names = (
    'subst',
    'verb',
    'adjadv',
    'praep',
    'definition',
    'phrase',
    'example',
)

#==============================================================================
# for translating setion names to target language (German) - not used here
#==============================================================================
sn_de ={'subst':"Substantiv",
    'verb':"Verb",
    'adjadv':"Adj./Adv.",
    'praep':"Praeposition",
    'definition':"Definition",
    'phrase':"Phrase",
    'example':"Beispiel",}

def _get_text(elt):
    buf = StringIO()

    def _helper(_elt):
        if _elt.text is not None:
            buf.write(str(_elt.text))
        for child in _elt:
            _helper(child)
        if _elt.tail is not None:
            buf.write(str(_elt.tail))

    _helper(elt)
    return buf.getvalue()


def search(term, lang='fr', timeout=None):
    '''term = search term
    lang = source language, one of en, es, it, fr, pt, ch, ru, pt, pl
    timeout = None or max. number of seconds to wait for response'''
    logger.info(f"searching term: {term}")
    sl = lang
    url = uri % (sl, tl)
    resp = requests.get(url, params={'search': term}, timeout=timeout)
    ret = {}
    if resp.status_code != requests.codes.ok:
        return ret
    p = etree.HTMLParser()
    html = etree.parse(StringIO(resp.text), p)
    for section_name in section_names:
        section = html.find(".//div[@id='section-%s']" % section_name)
        if section is None:
            continue
        ret[section_name] = []
        results = section.findall(".//td[@lang='%s']" % (sl,))  # source language
        for r_sl in results:
            r_tl = r_sl.find("./../td[@lang='%s']" % (tl,))     # target language
            ret[section_name].append({
                sl: _get_text(r_sl).strip(),
                tl: _get_text(r_tl).strip(),
            })
    return ret


if __name__ == '__main__':
    from sys import argv

    print(search(argv[1]))