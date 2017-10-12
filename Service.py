import ScholarPython as sc
import DblpPython as dblp
import requests
import web
import json
from bson.json_util import dumps

from pymongo import MongoClient


urls = (
    '/(.*)/author/(.*)/publications/(.*)', 'getPublications',
    '/(.*)/author/(.*)/coauthors', 'getCoauthors',
    '/(.*)/author/(.*)', 'getAuthor'
)

JSONERROR = "{'error':'Not Found'}"
JSONSOURCEERROR = "{'error':'Invalid Source'}"

client = MongoClient('localhost:27017')
db = client.eseco


class getAuthor:
    def GET(self,src, name):
        if src == 'scholar':
            try:
                authors = db.author.find()
                for author in authors:
                    if author['name'] == name:
                        del author['publications']
                        del author['_id']
                        return dumps(author)

                soup = sc.get_soup(sc.AUTHSEARCH.format(requests.utils.quote(name)))
                author = next(sc.search_citation_soup(soup)).fill()
            except:
                return JSONERROR
            else:
                try:
                    result = json.dumps(author.__dict__, default=obj_dict)
                    db.author.insert_one(json.loads(result))
                except:
                    pass
                return str(author)
        elif src == 'dblp':
            try:
                author = dblp.fill_author(name)
            except:
                return JSONERROR
            else:
                return author
        else:
            return JSONSOURCEERROR


class getPublications:
    def GET(self, src, name, citationsId=0):
        if src == 'scholar':
            try:
                flag = False
                authors = db.author.find()
                for auth in authors:
                    if auth['name'] == name:
                        author = auth
                        flag = True
                        break;

                if flag:
                    if citationsId == "":
                        return dumps(author['publications'])
                    else:
                        targetPub = None
                        for pub in author['publications']:
                            if pub['id_citations'] == citationsId:
                                targetPub = pub
                                break
                        if targetPub is not None:
                            pubs = db.publication.find()
                            for pub in pubs:
                                if pub['id_citations'] == citationsId:
                                    del pub['_id']
                                    return dumps(pub)

                soup = sc.get_soup(sc.AUTHSEARCH.format(requests.utils.quote(name)))
                author = next(sc.search_citation_soup(soup)).fill()

                if author is not None:
                    if citationsId == "":
                        return str(author.publications)
                    else:
                        targetPub = None
                        for pub in author.publications:
                            if pub.id_citations == citationsId:
                                targetPub = pub
                                break
                        if targetPub is not None:
                            targetPub.fill()
                            try:
                                result = json.dumps(targetPub.__dict__, default=obj_dict)
                                db.publication.insert_one(json.loads(result))
                            except:
                                pass
                            return str(targetPub)
                        else:
                            return JSONERROR
                else:
                    return JSONERROR
            except:
                return JSONERROR
        elif src == 'dblp':
            try:
                publications = dblp.fill_author(name).publications
            except:
                return JSONERROR
            else:
                return publications
        else:
            return JSONSOURCEERROR

class getCoauthors:
    def GET(self,src, name):
        if src == 'dblp':
            try:
                coauthors = dblp.fill_author(name).coauthors
            except:
                return JSONERROR
            else:
                return coauthors
        else:
            return JSONSOURCEERROR

def obj_dict(obj):
    return obj.__dict__

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()


