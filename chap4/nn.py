from math import tanh
import sqlite3


def dtanh(y):
    return 1.0 - y * y


class SearchNet(object):
    def __init__(self, db_name):
        self.con = sqlite3.connect(db_name)

    def __del__(self):
        self.con.close()

    def make_tables(self):
        self.con.execute('create table hidden_node(create_key)')
        self.con.execute('create table word_hidden(from_id, to_id, strength)')
        self.con.execute('create table hidden_url(from_id, to_id, strength)')
        self.con.commit()

    def get_strength(self, from_id, to_id, layer):
        if layer == 0:
            table = 'word_hidden'
        else:
            table = 'hidden_url'

        result = self.con.execute(
                'select strength from %s where from_id=%d and to_id=%d' %\
                        (table, from_id, to_id)).fetchone()
        if not result:
            if layer == 0:
                return -0.2
            if layer == 1:
                return 0

        return result[0]

    def set_strength(self, from_id, to_id, layer, strength):
        if layer == 0:
            table = 'word_hidden'
        else:
            table = 'hidden_url'

        result = self.con.execute(
                'select rowid from %s where from_id=%d and to_id=%d' %\
                        (table, from_id, to_id)).fetchone()
        if not result:
            self.con.execute(
                    'insert into %s (from_id, to_id, strength) values (%d, %d, %f)' %\
                            (table, from_id, to_id, strength))
        else:
            rowid = result[0]
            self.con.execute(
                    'update %s set strength=%f where rowid=%d' %\
                            (table, strength, rowid))

    def generate_hidden_node(self, word_ids, urls):
        if len(word_ids) > 3:
            return None
        create_key = '_'.join(sorted([str(wi) for wi in word_ids]))
        result = self.con.execute(
                'select rowid from hidden_node where create_key=\'%s\'' %\
                        create_key).fetchone()

        if not result:
            cur = self.con.execute(
                    'insert into hidden_node (create_key) values (\'%s\')' %\
                            create_key)
            hidden_id = cur.lastrowid
            for word_id in word_ids:
                self.set_strength(word_id, hidden_id, 0, 1.0 / len(word_ids))
            for url_id in urls:
                self.set_strength(hidden_id, url_id, 1, 0.1)

            self.con.commit()

    def get_all_hidden_ids(self, word_ids, url_ids):
        l1 = {}
        for word_id in word_ids:
            cur = self.con.execute(
                    'select to_id from word_hidden where from_id=%d' % word_id)
            for row in cur:
                l1[row[0]] = 1
        for url_id in url_ids:
            cur = self.con.execute(
                    'select from_id from hidden_url where to_id=%d' % url_id)
            for row in cur:
                l1[row[0]] = 1
        return l1.keys()

    def setup_network(self, word_ids, url_ids):
        self.word_ids = word_ids
        self.hidden_ids = self.get_all_hidden_ids(word_ids, url_ids)
        self.url_ids = url_ids

        self.ai = [1.0] * len(self.word_ids)
        self.ah = [1.0] * len(self.hidden_ids)
        self.ao = [1.0] * len(self.url_ids)

        self.wi = [[self.get_strength(word_id, hidden_id, 0)
            for hidden_id in self.hidden_ids]
            for word_id in self.word_ids]
        self.wo = [[self.get_strength(hidden_id, url_id, 1)
            for url_id in self.url_ids]
            for hidden_id in self.hidden_ids]

    def feed_forward(self):
        for i in xrange(len(self.word_ids)):
            self.ai[i] = 1.0

        for j in xrange(len(self.hidden_ids)):
            sum = 0.0
            for i in xrange(len(self.word_ids)):
                sum = sum + self.ai[i] * self.wi[i][j]
            self.ah[j] = tanh(sum)

        for k in xrange(len(self.url_ids)):
            sum = 0.0
            for j in xrange(len(self.hidden_ids)):
                sum = sum + self.ah[j] * self.wo[j][k]
            self.ao[k] = tanh(sum)

        return self.ao[:]

    def get_result(self, word_ids, url_ids):
        self.setup_network(word_ids, url_ids)
        return self.feed_forward()

    def back_propagate(self, targets, N=0.5):
        output_deltas = [0.0] * len(self.url_ids)
        for k in xrange(len(self.url_ids)):
            error = targets[k] - self.ao[k]
            output_deltas[k] = dtanh(self.ao[k]) * error

        hidden_deltas = [0.0] * len(self.hidden_ids)
        for j in xrange(len(self.hidden_ids)):
            error = 0.0
            for k in xrange(len(self.url_ids)):
                error = error + output_deltas[k] * self.wo[j][k]

            hidden_deltas[j] = dtanh(self.ah[j]) * error

        for j in xrange(len(self.hidden_ids)):
            for k in xrange(len(self.url_ids)):
                change = output_deltas[k] * self.ah[j]
                self.wo[j][k] = self.wo[j][k] + N * change

        for i in xrange(len(self.word_ids)):
            for j in xrange(len(self.hidden_ids)):
                change = hidden_deltas[j] * self.ai[i]
                self.wi[i][j] = self.wi[i][j] + N * change

    def train_query(self, word_ids, url_ids, selected_url):
        self.generate_hidden_node(word_ids, url_ids)

        self.setup_network(word_ids, url_ids)
        self.feed_forward()

        targets = [0.0] * len(url_ids)
        targets[url_ids.index(selected_url)] = 1.0

        error = self.back_propagate(targets)
        self.update_database()
    
    def update_database(self):
        for i in xrange(len(self.word_ids)):
            for j in xrange(len(self.hidden_ids)):
                self.set_strength(self.word_ids[i], self.hidden_ids[j], 0, self.wi[i][j])

        for j in xrange(len(self.hidden_ids)):
            for k in xrange(len(self.url_ids)):
                self.set_strength(self.hidden_ids[j], self.url_ids[k], 1, self.wo[j][k])

        self.con.commit()

