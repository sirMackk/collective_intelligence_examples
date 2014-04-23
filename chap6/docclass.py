import re
import math
import sqlite3


def get_words(doc):
    '''
    This is a helper function that splits a string into
    words that are longer than 2 chars and shorter than 20.
    '''
    splitter = re.compile('\\W*')
    words = [s.lower() for s in splitter.split(doc)
                if len(s) > 2 and len(s) < 20]

    return dict([(w, 1) for w in words])


class Classifier(object):
    def __init__(self, get_features, file_name=None):
        self.feature_category = {}
        self.document_in_category = {}
        self.get_features = get_features
        self.thresholds = {}

    def set_db(self, db_file):
        self.con = sqlite3.connect(db_file)
        self.con.execute('create table if not exists \
                feature_category(feature, category, count)')
        self.con.execute('create table if not exists \
                document_in_category(category, count)')

    def incf(self, feature, category):
        '''
        This increases the category-count for a given category for the
        supplied feature. Basically, it shows how many times a feature 
        has been placed in each category. For the purposes of the
        Programming Collective Intelligence book, this would look
        like {'quick': {'good': 2, 'bad': 1}}.
        '''
        # commented out functionality that works using dicts instead of sqlit
        #self.feature_category.setdefault(feature, {})
        #self.feature_category[feature].setdefault(category, 0)
        #self.feature_category[feature][category] += 1
        count = self.f_count(feature, category)
        if count == 0:
            self.con.execute('insert into feature_category values \
                    ("%s", "%s", 1)' % (feature, category))
        else:
            self.con.execute('update feature_category set count = %d \
                    where feature = "%s" and category = "%s"' %
                    (count + 1, feature, category))

    def incc(self, category):
        '''
        Increases the count for each category.
        '''
        # commented out functionality that works using dicts instead of sqlit
        #self.document_in_category.setdefault(category, 0)
        #self.document_in_category[category] += 1
        count = self.cat_count(category)
        if count == 0:
            self.con.execute('insert into document_in_category values \
                    ("%s", 1)' % category)
        else:
            self.con.execute('update document_in_category set count = %d \
                    where category = "%s"' % (count + 1, category))

    def f_count(self, feature, category):
        '''
        Retrieves the count for the supplied category and feature.
        '''
        # commented out functionality that works using dicts instead of sqlit
        #if feature in self.feature_category and category in self.feature_category[feature]:
            #return float(self.feature_category[feature][category])
        #return 0.0
        res = self.con.execute('select count from feature_category\
                 where feature = "%s" and category = "%s"' %
                 (feature, category)).fetchone()
        if not res:
            return 0
        else:
            return float(res[0])

    def cat_count(self, category):
        '''
        Retrieves the count for the specified category.
        '''
        # commented out functionality that works using dicts instead of sqlit
        #if category in self.document_in_category:
            #return float(self.document_in_category[category])
        #return 0.0
        res = self.con.execute('select count from document_in_category \
                where category = "%s"' % category).fetchone()
        if not res:
            return 0
        else:
            return float(res[0])

    def total_count(self):
        '''
        Retrieves the total count for all categories.
        '''
        # commented out functionality that works using dicts instead of sqlit
        #return sum(self.document_in_category.values())
        res = self.con.execute('select sum(count) from document_in_category').fetchone()
        if not res:
            return 0
        else:
            return res[0]

    def categories(self):
        '''
        Retrieves all categories.
        '''
        # commented out functionality that works using dicts instead of sqlit
        #return self.document_in_category.keys()
        cur = self.con.execute('select category from document_in_category')
        return [d[0] for d in cur]

    def train(self, item, category):
        '''
        This functions uses the self.get_features function to extract
        features from a supplied item. It then iterates through all
        of the features and increases the feature_category count
        for each feature for the supplied category. Finally, it increases
        the category count.
        '''
        features = self.get_features(item)
        for feature in features:
            self.incf(feature, category)

        self.incc(category)
        self.con.commit()

    def f_prob(self, feature, category):
        '''
        Returns the count of a feature for a supplied category
        divided by the size of the category.
        '''
        if self.cat_count(category) == 0:
            return 0

        return self.f_count(feature, category) / self.cat_count(category)

    def weighted_prob(self, feature, category, prf, weight=1.0, ap=0.5):
        '''
        We first obtain the basic probability for a feature in a category
        (usually using the f_prob fn). Then we use bayes theorem to
        obtain an initial approximate probability that the feature
        belongs to the supplied category.
        '''
        basic_prob = prf(feature, category)

        totals = sum([self.f_count(feature, category) for c in self.categories()])

        weighted = ((weight * ap) + (totals * basic_prob)) / (weight + totals)
        return weighted

    def set_threshold(self, category, t):
        self.thresholds[category] = t

    def get_threshold(self, category):
        if category not in self.thresholds:
            return 1.0
        return self.thresholds[category]


class NaiveBayes(Classifier):
    def doc_prob(self, item, category):
        '''
        Extracts all the features from a supplied item
        and then multiplies all of their probabilities (belonging to
        a category) into one.
        '''
        features = self.get_features(item)

        p = 1
        for feature in features:
            p *= self.weighted_prob(feature, category, self.f_prob)
        return p

    def prob(self, item, category):
        '''
        First, get the ratio of the supplied category and total categories.
        Then get the probability of the item belonging to that category
        using self.doc_prob. Finally, multiply these items to
        get the probability of the item belonging to that category
        given the category.
        '''
        cat_prob = self.cat_count(category) / self.total_count()
        doc_prob = self.doc_prob(item, category)
        return doc_prob * cat_prob

    def classify(self, item, default=None):
        '''
        We iterate through the categories in our classifier
        and check how the supplied item matches each category.
        During the matching, we update the best matched category.
        Then we run the categories through the thresholds and finally
        we return the best matching category for the item.
        '''
        probs = {}
        max = 0.0
        for category in self.categories():
            probs[category] = self.prob(item, category)
            if probs[category] > max:
                max = probs[category]
                best = category

        for category in probs:
            if category == best:
                continue
            if probs[category] * self.get_threshold(best) > probs[best]:
                return default
        return best


class FisherClassifier(Classifier):
    def __init__(self, get_features):
        Classifier.__init__(self, get_features)
        self.minimums = {}

    def c_prob(self, feature, category):
        '''
        Calculate the frequency of a feature in the supplied
        category.
        '''
        clf = self.f_prob(feature, category)
        if clf == 0:
            return 0

        freq_sum = sum([self.f_prob(feature, cat) for cat in self.categories()])

        p = clf / freq_sum

        return p

    def fisher_prob(self, item, category):
        '''
        First, get all the probabilities for each feature for the supplied
        category. Then take the log of that and multiply by -2 and
        run the result through an inverse chi squared function.
        '''
        p = 1.0
        features = self.get_features(item)
        for feature in features:
            p *= (self.weighted_prob(feature, category, self.c_prob))

        f_score = -2 * math.log(p)

        return self.inv_chi2(f_score, len(features) * 2)

    def inv_chi2(self, chi, df):
        '''
        Inverse chi squared function.
        https://en.wikipedia.org/wiki/Inverse-chi-squared_distribution
        '''
        m = chi / 2.0
        sum = term = math.exp(-m)
        for i in xrange(1, df // 2):
            term *= m / i
            sum += term

        return min(sum, 1.0)

    def set_minimum(self, category, min):
        self.minimums[category] = min

    def get_minimum(self, category):
        if category not in self.minimums:
            return 0
        return self.minimums[category]

    def classify(self, item, default=None):
        '''
        Iterate through all the categories and return
        the category for which the probability of matching
        is the highest.
        '''
        best = default
        max = 0.0
        for category in self.categories():
            p = self.fisher_prob(item, category)
            if p > self.get_minimum(category) and p > max:
                best = category
                max = p

        return best


def sample_train(classifier):
    '''
    This is a helper function that trains the supplied classifier.
    '''
    classifier.train('Nobody owns the water.', 'good')
    classifier.train('the quick rabbit jumps fences', 'good')
    classifier.train('buy pharmaceuticals now', 'bad')
    classifier.train('make quick money at the online casino', 'bad')
    classifier.train('the quick brown fox jumps', 'good')
