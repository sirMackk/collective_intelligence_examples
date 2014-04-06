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
        '''
        Retrieves the strength field value from the appropriate table.
        '''
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
        '''
        Sets the strength field for the appropriate table and row.
        Adds row if row is not found.
        '''
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
        '''
        Checks if a hidden node already exists and if not it creates one
        by inserting it into the hidden_node table. Then it creates an
        entry in the word_hidden table linking each word of the query
        with the hidden_table entry. Afterwards, it creates an entry in
        the hidden_url table linking each url of the results with the hidden
        table entry.
        '''
        if len(word_ids) > 3:
            return None
        # creates a unique key for a sequence of words
        create_key = '_'.join(sorted([str(wi) for wi in word_ids]))
        result = self.con.execute(
                'select rowid from hidden_node where create_key=\'%s\'' %\
                        create_key).fetchone()

        if not result:
            cur = self.con.execute(
                    'insert into hidden_node (create_key) values (\'%s\')' %\
                            create_key)
            hidden_id = cur.lastrowid
            # link query words with the hidden node
            for word_id in word_ids:
                self.set_strength(word_id, hidden_id, 0, 1.0 / len(word_ids))
            # link resulting urls with the hidden node
            for url_id in urls:
                self.set_strength(hidden_id, url_id, 1, 0.1)

            self.con.commit()

    def get_all_hidden_ids(self, word_ids, url_ids):
        '''
        Returns all of the hidden node id's that are associated with
        a list of words and a list of queries.
        '''
        l1 = {}
        # gets all the hidden node id's that are linked to a word (query)
        for word_id in word_ids:
            cur = self.con.execute(
                    'select to_id from word_hidden where from_id=%d' % word_id)
            for row in cur:
                l1[row[0]] = 1
        # gets all the hidden node id's that are linked to a url (result)
        for url_id in url_ids:
            cur = self.con.execute(
                    'select from_id from hidden_url where to_id=%d' % url_id)
            for row in cur:
                l1[row[0]] = 1
        return l1.keys()

    def setup_network(self, word_ids, url_ids):
        '''
        Prepares instance variables associated with a query and it's results
        to be used in feed_forward and back_propagate.
        '''
        self.word_ids = word_ids
        self.hidden_ids = self.get_all_hidden_ids(word_ids, url_ids)
        self.url_ids = url_ids

        # sets up lists of output for each layer:
        # ai - input nodes, ah - hidden nodes, ao - output nodes
        self.ai = [1.0] * len(self.word_ids)
        self.ah = [1.0] * len(self.hidden_ids)
        self.ao = [1.0] * len(self.url_ids)

        # creates weights matrices:
        # wi - gets strengths of each hidden node for each word (query)
        self.wi = [[self.get_strength(word_id, hidden_id, 0)
            for hidden_id in self.hidden_ids]
            for word_id in self.word_ids]
        # wo - gets strengths for each hidden_node for each url (result)
        self.wo = [[self.get_strength(hidden_id, url_id, 1)
            for url_id in self.url_ids]
            for hidden_id in self.hidden_ids]

    def feed_forward(self):
        '''
        This returns the output of all the output nodes, with the inputs
        coming from the setup_network function.
        '''
        # first it sets the input word weights to 1.0
        for i in xrange(len(self.word_ids)):
            self.ai[i] = 1.0

        # then it iterates through all of the hidden nodes associated with
        # the words and urls (query and results) and uses a sigmoid to
        # accumulate the weights coming from the inputs (ai) and the
        # input weight matrix (wi) for each word-hidden_node relation.
        for j in xrange(len(self.hidden_ids)):
            sum = 0.0
            for i in xrange(len(self.word_ids)):
                sum = sum + self.ai[i] * self.wi[i][j]
            self.ah[j] = tanh(sum)

        # finally it iterates through all of the output nodes (urls)
        # and uses a sigmoid function to accumulate the weights
        # coming from the hidden nodes (ah) updated in the
        # previous step and the output weights (wo) for each
        # hidden_node-url relation.
        for k in xrange(len(self.url_ids)):
            sum = 0.0
            for j in xrange(len(self.hidden_ids)):
                sum = sum + self.ah[j] * self.wo[j][k]
            self.ao[k] = tanh(sum)

        return self.ao[:]

    def get_result(self, word_ids, url_ids):
        '''
        Having a list of input and outputs, this function first sets up
        the required instance variables (hidden node list, input/output
        weight matrices) and runs those through the feed_forward function
        to obtain the weights for each output ie. which output
        is the most likely.
        '''
        self.setup_network(word_ids, url_ids)
        return self.feed_forward()

    def back_propagate(self, targets, N=0.5):
        '''
        Using the existing node strengths as well as the selected target,
        we check how much the output and input strengths should be changed
        and saved into the neural network.
        '''
        # first calculate how much the current output nodes have to change
        # relative to the stored output strengths.
        output_deltas = [0.0] * len(self.url_ids)
        for k in xrange(len(self.url_ids)):
            error = targets[k] - self.ao[k]
            output_deltas[k] = dtanh(self.ao[k]) * error

        # then sum the outputs for each hidden node and calculate how much
        # the hidden nodes have to change.
        hidden_deltas = [0.0] * len(self.hidden_ids)
        for j in xrange(len(self.hidden_ids)):
            error = 0.0
            for k in xrange(len(self.url_ids)):
                error = error + output_deltas[k] * self.wo[j][k]

            hidden_deltas[j] = dtanh(self.ah[j]) * error

        # update the output weight matrix using the output_deltas
        # and hidden nodes and the weight N.
        for j in xrange(len(self.hidden_ids)):
            for k in xrange(len(self.url_ids)):
                change = output_deltas[k] * self.ah[j]
                self.wo[j][k] = self.wo[j][k] + N * change

        # update the input weight matrix using the hidden_deltas
        # and input nodes and the weight N
        for i in xrange(len(self.word_ids)):
            for j in xrange(len(self.hidden_ids)):
                change = hidden_deltas[j] * self.ai[i]
                self.wi[i][j] = self.wi[i][j] + N * change

    def train_query(self, word_ids, url_ids, selected_url):
        '''
        Having a set of input words (query) and output urls (urls)
        AND which url was selected, this function will strengthen
        a certain hidden_node.
        '''
        # first ensure that the input, output, and hidden nodes
        # exist for the query and results.
        self.generate_hidden_node(word_ids, url_ids)

        # then create instance variables holding the hidden_node list
        # and the weight matrices.
        self.setup_network(word_ids, url_ids)
        # then obtain the current weights of the hidden and output nodes
        # using the feedforward function.
        self.feed_forward()

        # then create a list of outputs all set to 0.0 and set the selected
        # url (at the index) to 1.0
        targets = [0.0] * len(url_ids)
        targets[url_ids.index(selected_url)] = 1.0

        # feed the targets to the backpropagate function to generate new
        # new weight matrices
        error = self.back_propagate(targets)
        # update the strength columns in the table for both input and outputs
        self.update_database()
    
    def update_database(self):
        '''
        Updates database with new node strengths.
        '''
        # update the word_hidden table with new input strengths
        for i in xrange(len(self.word_ids)):
            for j in xrange(len(self.hidden_ids)):
                self.set_strength(self.word_ids[i], self.hidden_ids[j], 0, self.wi[i][j])

        # update the hidden_url table with new output strengths
        for j in xrange(len(self.hidden_ids)):
            for k in xrange(len(self.url_ids)):
                self.set_strength(self.hidden_ids[j], self.url_ids[k], 1, self.wo[j][k])

        self.con.commit()

