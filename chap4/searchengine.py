import urllib2
from bs4 import BeautifulSoup
from urlparse import urljoin
import sqlite3
import re
import nn

mynet = nn.SearchNet('nn.db')

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
        '''
        This method attempts to retrieve the primary key rowid of an
        entry in 'table' where 'field' equals 'value'.
        If it cannot find this entry, it creates it and returns the rowid.
        '''
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
        '''
        Registers the url in the url_list, then registers every word
        (using soup) with it's url, word_id and location in the page.
        '''
        if self.is_indexed(url):
            return

        #print 'Indexing %s' % url

        text = self.get_text_only(soup)
        words = self.separate_words(text)

        # retrieves or sets and retrieves a url's rowid
        url_id = self.get_entry_id('url_list', 'url', url)

        # iterates through all the words under a given url
        for i in xrange(len(words)):
            word = words[i]
            if word in ignore_words:
                continue
            # retrieves or sets and retrieves a word's rowid
            word_id = self.get_entry_id('word_list', 'word', word)
            # record the url and word (by id) and location (by index of the
            # in all the words on a page)
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
        '''
        This function accepts a string and returns a list of lower-case
        words.
        '''
        splitter = re.compile('\\W*')
        return [s.lower() for s in splitter.split(text) if s != '']

    def is_indexed(self, url):
        '''
        This function checks if a url has been entered into the url_list
        table and if yes, then further checks if an entry has been made
        in the word_location table for that url and if these two conditions
        are met - it returns True. Otherwise False.
        '''
        u = self.con.execute('select rowid from url_list where url = \'%s\''
                % url).fetchone()
        if u:
            v = self.con.execute('select * from word_location where url_id\
                    =%d' % u[0]).fetchone()
            if v:
                return True
        return False

    def add_link_ref(self, url_from, url_to, link_text):
        '''
        This function uses the to and from urls to add an entry to the link
        table. Then it uses the newly created row's rowid, it registers
        each word of the link text with the link entry in the link table.
        '''
        words = self.separate_words(link_text)
        from_id = self.get_entry_id('url_list', 'url', url_from)
        to_id = self.get_entry_id('url_list', 'url', url_to)
        # ensure that the page isnt linking to itself
        if from_id == to_id:
            return
        # add entry to the link table, which shows the url_ids of the
        # linking and linked pages
        cur = self.con.execute(
                'insert into link(from_id, to_id) values (%d, %d)' % \
                        (from_id, to_id))
        link_id = cur.lastrowid
        for word in words:
            if word in ignore_words:
                continue
            word_id = self.get_entry_id('word_list', 'word', word)
            # add entry to the link_words table, which shows what words are
            # associated with what links.
            self.con.execute(
                    'insert into link_words(link_id, word_id) values (%d, %d)'\
                            % (link_id, word_id))

    def crawl(self, pages, depth=2):
        '''
        This function, given a list of urls, opens each url and then
        proceeds to process it and add it to the appropriate tables
        in the database.
        '''
        for i in xrange(depth):
            new_pages = set()
            for page in pages:
                try:
                    document = urllib2.urlopen(page)
                except:
                    print "Could not open %s page" % page
                    continue
                soup = BeautifulSoup(document.read())
                # process a page and record the findings in the db
                self.add_to_index(page, soup)

                # scrape all the links from the page
                links = soup('a')
                for link in links:
                    if 'href' in dict(link.attrs):
                        # use urlpar.urljoin to combine user-provided
                        # absolute url and the anchor address scraped.
                        url = urljoin(page, link['href'])
                        # continue loop if a single quote mark is in the url
                        if url.find("'") != -1:
                            continue
                        url = url.split("#")[0]
                        if url[0:4] == 'file' or url[0:4] == 'http' and not self.is_indexed(url):
                            # if the url hasnt been indexed yet, then add it
                            # to the new_pages set. Using a set ensures that
                            # there will be no duplicates
                            new_pages.add(url)
                            link_text = self.get_text_only(link)
                            # use the current page url (page), the linked
                            # url (url), and the link text to add an entry
                            # to the link_words table
                            self.add_link_ref(page, url, link_text)
                self.db_commit()

                pages = new_pages

    def calculate_page_rank(self, iterations=20):
        self.con.execute('drop table if exists page_rank')
        self.con.execute('create table page_rank(url_id primary key, score)')

        self.con.execute(
                'insert into page_rank select rowid, 1.0 from url_list')
        self.db_commit()

        for i in xrange(iterations):
            print 'Iteration: %d' % i
            for (url_id,) in self.con.execute('select rowid from url_list'):
                pr = 0.15

                for (linker,) in self.con.execute(
                        'select distinct from_id from link where to_id=%d' % \
                                url_id):
                    linking_pr = self.con.execute(
                            'select score from page_rank where url_id=%d' % \
                                    linker).fetchone()[0]

                    linking_count = self.con.execute(
                            'select count(*) from link where from_id=%d' % \
                                    linker).fetchone()[0]
                    pr += 0.85 * (linking_pr / linking_count)

                self.con.execute(
                        'update page_rank set score=%f where url_id=%d' % \
                            (pr, url_id))

        self.db_commit()

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

    def get_match_rows(self, q):
        '''
        This function builds a long sql query that selects the url_id
        and locations for all the words for all pages (urls) that share
        the words in the query q.
        This is later returned as a list of rows, where each row looks
        something like: [url_id, word 0 location, word 1 location, ... ]
        '''
        field_list = 'w0.url_id'
        table_list = ''
        clause_list = ''
        word_ids = []

        words = q.split()
        table_number = 0

        for word in words:
            word_row = self.con.execute('select rowid from word_list \
                    where word=\'%s\'' % word).fetchone()
            if word_row:
                word_id = word_row[0]
                word_ids.append(word_id)
                # if there is more than 1 word in the query, we will break
                # the table list apart with a comma and the clause list
                # with an AND. We then add the clause that both queries
                # should affect the same url (url_id = url_id)
                if table_number > 0:
                    table_list += ','
                    clause_list += ' and '
                    clause_list += 'w%d.url_id=w%d.url_id and ' % \
                        (table_number - 1, table_number)
                field_list += ' ,w%d.location' % table_number
                table_list += 'word_location w%d' % table_number
                clause_list += 'w%d.word_id=%d' % (table_number, word_id)
                table_number += 1

        full_query = 'select %s from %s where %s' % \
                (field_list, table_list, clause_list)
        # execute the built query, which will return url_ids paired with
        # a words location under that url for only the urls, which contain
        # all of the specified words.
        cur = self.con.execute(full_query)
        rows = [row for row in cur]

        return rows, word_ids

    def get_scored_list(self, rows, word_ids):
        '''
        Applies the list of weights to the results of get_match_rows.
        Returns a list of urls with each normalized score added to
        each url.
        '''

        total_scores = dict([(row[0], 0) for row in rows])

        #weights = [(1.0, self.frequency_score(rows))]
        #weights = [(1.0, self.location_score(rows))]
        #weights = [(1.0, self.frequency_score(rows)), (1.5, self.location_score(rows))]
        #weights = [(1.0, self.location_score(rows)), (1.8, self.inbound_link_score(rows))]
        weights = [(1.0, self.location_score(rows)),
                (1.0, self.frequency_score(rows)),
                (1.0, self.page_rank_score(rows)),
                (1.0, self.link_text_score(rows, word_ids))]


        for (weight, scores) in weights:
            for url in total_scores:
                total_scores[url] += weight * scores[url]

        return total_scores

    def get_url_name(self, id):
        '''
        Retrieves the url given a url_list rowid.
        '''
        return self.con.execute(
                'select url from url_list where rowid=%d' % id).fetchone()[0]

    def query(self, q):
        '''
        First it finds the relevent rows of urls that match the query q,
        then it applies scoring and weighing to those urls, and finally
        returns a sorted list with string urls for readability.
        '''
        rows, word_ids = self.get_match_rows(q)
        scores = self.get_scored_list(rows, word_ids)
        ranked_scores = sorted([(score, url)
            for (url, score) in scores.items()], reverse=True)
        for (score, url_id) in ranked_scores[:10]:
            print '%f\t%s' % (score, self.get_url_name(url_id))

        return word_ids, [r[1] for r in ranked_scores[:10]]

    def normalize_scores(self, scores, small_is_better=False):
        '''
        It divides each score by the total number of scores for this category,
        so that different scoring methods all supply a unified score.
        '''
        vsmall = 0.00001
        if small_is_better:
            min_score = min(scores.values())
            return dict([(u, float(min_score) / max(vsmall, l))
                for (u, l) in scores.items()])
        else:
            max_score = max(scores.values())
            if max_score == 0:
                max_score = vsmall
            return dict([(u, float(c) / max_score) for (u, c) in scores.items()])

    # simple scoring methods

    def frequency_score(self, rows):
        counts = dict([(row[0], 0) for row in rows])
        for row in rows:
            counts[row[0]] += 1
        return self.normalize_scores(counts)

    def location_score(self, rows):
        locations = dict([(row[0], 1000000) for row in rows])
        for row in rows:
            loc = sum(row[1:])
            if loc < locations[row[0]]:
                locations[row[0]] = loc

        return self.normalize_scores(locations, small_is_better=True)

    def distance_score(self, rows):
        if len(rows[0]) <= 2:
            return dict([(row[0], 1.0) for row in rows])

        min_distance = dict([(row[0], 1000000) for row in rows])

        for row in rows:
            dist = sum([abs(row[i] - row[i-1]) for i in xrange(2, len(row))])
            if dist < min_distance[row[0]]:
                min_distance[row[0]] = dist
        return self.normalize_scores(min_distance, small_is_better=True)

    # inbound links scoring methods

    def inbound_link_score(self, rows):
        unique_urls = set([row[0] for row in rows])
        inbound_count = dict([(u, self.con.execute(
            'select count(*) from link where to_id=%d' % u).fetchone()[0]) 
            for u in unique_urls])
        return self.normalize_scores(inbound_count)

    def page_rank_score(self, rows):
        page_ranks = dict([(row[0], self.con.execute('select score from page_rank \
                where url_id=%d' % row[0]).fetchone()[0])
                for row in rows])
        max_rank = max(page_ranks.values())
        normalized_scores = dict([(u, float(l) / max_rank)
            for (u, l) in page_ranks.items()])
        return normalized_scores

    def link_text_score(self, rows, word_ids):
        link_scores = dict([(row[0], 0) for row in rows])
        for word_id in word_ids:
            cur = self.con.execute(
                    'select link.from_id, link.to_id from link_words, link \
                            where word_id=%d and link_words.link_id=link.rowid'\
                            % word_id)
            for (from_id, to_id) in cur:
                if to_id in link_scores:
                    pr = self.con.execute(
                            'select score from page_rank where url_id=%d' % \
                                    from_id).fetchone()[0]
                    link_scores[to_id] += pr
            max_score = max(link_scores.values())
            normalized_scores = dict([(u, float(l) / max_score)
                for (u, l) in link_scores.items()])
            return normalized_scores

    # neural network scoring

    def nn_score(self, rows, word_ids):
        url_ids = [url_id for url_id in set([row[0] for row in rows])]
        nn_result = mynet.get_result(word_ids, url_ids)
        scores = dict([(url_ids[i], nn_result[i]) for i in xrange(len(url_ids))])
        return self.normalize_scores(scores)

