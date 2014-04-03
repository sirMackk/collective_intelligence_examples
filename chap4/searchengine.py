import urllib2
from bs4 import BeautifulSoup
from urlparse import urljoin
import sqlite3
import re

ignore_words = {'the': 1, 'of': 1, 'to': 1, 'and': 1,
                'a': 1, 'in': 1, 'is': 1, 'it': 1}


class Crawler(object):
    def __init__(self, dbname):
        self.con = sqlite3.connect(dbname)

    def __del__(self):
        self.con.close()

    def db_commit(self):
        self.con.commit()

    def get_entry_id(self, table, field, value, create_new=True):
        cur = self.con.execute('select rowid from %s where %s=\'%s\'' %
                (table, field, value))
        result = cur.fetchone()
        if not result:
            cur = self.con.execute('insert into %s (%s) values (\'%s\')' %
                    (table, field, value))
            return cur.lastrowid
        else:
            return result[0]

    def add_to_index(self, url, soup):
        if self.is_indexed(url):
            return

        #print 'Indexing %s' % url

        text = self.get_text_only(soup)
        words = self.separate_words(text)

        url_id = self.get_entry_id('url_list', 'url', url)

        for i in xrange(len(words)):
            word = words[i]
            if word in ignore_words:
                continue
            word_id = self.get_entry_id('word_list', 'word', word)
            self.con.execute('insert into word_location(url_id, word_id, location) \
                    values (%d, %d, %d)' % (url_id, word_id, i))

    def get_text_only(self, soup):
        '''
        Traverses down the DOM and collects the the page into a long string.
        '''
        v = soup.string
        if not v:
            c = soup.contents
            result_text = [self.get_text_only(t) for t in c]
            return '\n'.join(result_text)
        else:
            return v.strip()
        return None

    def separate_words(self, text):
        splitter = re.compile('\\W*')
        return [s.lower() for s in splitter.split(text) if s != '']

    def is_indexed(self, url):
        u = self.con.execute('select rowid from url_list where url = \'%s\''
                % url).fetchone()
        if u:
            v = self.con.execute('select * from word_location where url_id\
                    =%d' % u[0]).fetchone()
            if v:
                return True
        return False

    def add_link_ref(self, url_from, url_to, link_text):
        pass

    def crawl(self, pages, depth=2):
        for i in xrange(depth):
            new_pages = set()
            for page in pages:
                try:
                    document = urllib2.urlopen(page)
                except:
                    print "Could not open %s page" % page
                    continue
                soup = BeautifulSoup(document.read())
                self.add_to_index(page, soup)

                links = soup('a')
                for link in links:
                    if 'href' in dict(link.attrs):
                        url = urljoin(page, link['href'])
                        if url.find("'") != -1:
                            continue
                        url = url.split("#")[0]
                        if url[0:4] == 'file' or url[0:4] == 'http' and not self.is_indexed(url):
                            new_pages.add(url)
                            link_text = self.get_text_only(link)
                            self.add_link_ref(page, url, link_text)
                self.db_commit()

                pages = new_pages
        pass

    def create_index_tables(self):
        self.con.execute('create table url_list(url)')
        self.con.execute('create table word_list(word)')
        self.con.execute('create table word_location(url_id, word_id, location)')
        self.con.execute('create table link(from_id integer, to_id integer)')
        self.con.execute('create table link_words(word_id, link_id)')
        self.con.execute('create index url_idx on url_list(url)')
        self.con.execute('create index word_idx on word_list(word)')
        self.con.execute('create index word_url_idx on word_location(word_id)')
        self.con.execute('create index url_to_idx on link(to_id)')
        self.con.execute('create index url_from_idx on link(from_id)')
        self.db_commit()


class Searcher(object):
    def __init__(self, db_name):
        self.con = sqlite3.connect(db_name)

    def __del__(self):
        self.con.close()

