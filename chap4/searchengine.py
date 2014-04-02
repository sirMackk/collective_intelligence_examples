import urllib2
from BeautifulSoup import *
from urlparse import urljoin


class Crawler(object):
    def __init__(self, dbname):
        pass

    def __del__(self):
        pass

    def db_commit(self):
        pass

    def get_entry_id(self, table, field, value, create_new=True):
        return None

    def add_to_index(self, url, soup):
        print 'Indexing %s' % url

    def get_text_only(self, soup):
        return None

    def separate_words(self, text):
        return None

    def is_indexed(self, url):
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
                        if url.find("'") != 1:
                            continue
                        url = url.split("#")[0]
                        if url[0:4] == 'http' and not self.is_indexed(url):
                            new_pages.add(url)
                            link_text = self.get_text_only(link)
                            self.add_link_ref(page, url, link_text)
                self.db_commit()

                pages = new_pages
        pass

    def create_index_tables(self):
        pass
