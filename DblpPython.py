from __future__ import absolute_import, division, print_function, unicode_literals

import requests
import xmltodict, json
from difflib import SequenceMatcher

_DBLPSEARCH = 'http://dblp.uni-trier.de'
_AUTHSEARCH = '/search/author?xauthor='
_FULLSEARCH = '/pers/xx/'
_COAUTHSEARCH = '/pers/xc/'
_SESSION = requests.Session()
_HEADERS = {
    'accept-language': 'pt-BR,pt',
    'User-Agent': 'Mozilla/5.0',
    'accept': 'text/html,application/xhtml+xml,application/xml',

}


class Author(object):
    def __init__(self, __data):
        self.urlPt = __data['@urlpt']
        self.text = __data['#text']
        self._filled = False

    def fill(self):
        resp_full_url = _SESSION.get(_DBLPSEARCH + _FULLSEARCH + self.urlPt, headers=_HEADERS)
        resp_coauth_url = _SESSION.get(_DBLPSEARCH + _COAUTHSEARCH + self.urlPt, headers=_HEADERS)

        author_dic = xmltodict.parse(resp_full_url.text)
        coauthor_dic = xmltodict.parse(resp_coauth_url.text)

        coauthor_dic = dict(coauthor_dic)

        self.name = author_dic['dblpperson']['@name']
        self.publications = list()
        self.coauthors = list()
        self.pubCount = len(author_dic['dblpperson']['r'])
        self.coauthCount = len(author_dic['dblpperson']['coauthors']['co'])

        publications = author_dic['dblpperson']['r']

        for publication in publications:
            pub = Publication(publication)
            self.publications.append(pub)

        coauthors = coauthor_dic['coauthors']['author']

        for coauthor in coauthors:
            coauth = CoAuthor(coauthor)
            self.coauthors.append(coauth)

        self.coauthors.sort(key=lambda x: x.count, reverse=True)

        self._filled = True
        return self

    def __str__(self):
        d = dict(self.__dict__)
        if len(self.publications) > 0:
            del d['publications']
        if len(self.coauthors) > 0:
            del d['coauthors']
        return json.dumps(d, sort_keys=True, indent=4, separators=(',', ': '))


class Publication(object):
    def __init__(self, __data):
        for key in __data:
            self.type = key
            self.key = __data[key].get('@key', None)
            self.date = __data[key].get('@mdate', None)
            self.authors = list()
            self.title = __data[key].get('@title', None)
            self.pages = __data[key].get('pages', None)
            self.year = __data[key].get('year', None)
            self.volume = __data[key].get('volume', None)
            self.journal = __data[key].get('journal', None)
            self.booktitle = __data[key].get('booktitle', None)
            self.url = __data[key].get('ee', None)

            authors = __data[key]['author']

            for author in authors:
                self.authors.append(author)

    def __str__(self):
        d = dict(self.__dict__)
        return json.dumps(d, sort_keys=True, indent=4, separators=(',', ': '))

    def __repr__(self):
        return json.dumps(self.__dict__, sort_keys=True, indent=4, separators=(',', ': '))


class CoAuthor(object):
    def __init__(self, __data):
        self.name = __data['#text']
        self.count = int( __data['@count'])
        self.urlpt = __data['@urlpt']

    def __str__(self):
        d = dict(self.__dict__)
        return json.dumps(d, sort_keys=True, indent=4, separators=(',', ': '))

    def __repr__(self):
        return json.dumps(self.__dict__, sort_keys=True, indent=4, separators=(',', ': '))


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def fill_author(name):
    resp_url = _SESSION.get(_DBLPSEARCH+_AUTHSEARCH+name, headers=_HEADERS)
    author_dic = xmltodict.parse(resp_url.content)
    authors = author_dic['authors']['author']
    selected_author = authors[0]
    best_similarity = 0.0

    for author in authors:
        similarity = similar(author['#text'],name)
        if similarity > best_similarity:
            best_similarity = similarity
            selected_author = author

    selected_author = Author(selected_author)
    selected_author.fill()

    return selected_author

