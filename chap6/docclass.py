import re
import math


def get_words(doc):
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

    def incf(self, feature, category):
        self.feature_category.setdefault(feature, {})
        self.feature_category[feature].setdefault(category, 0)
        self.feature_category[feature][category] += 1

    def incc(self, category):
        self.document_in_category.setdefault(category, 0)
        self.document_in_category[category] += 1

    def f_count(self, feature, category):
        if feature in self.feature_category and category in self.feature_category[feature]:
            return float(self.feature_category[feature][category])
        return 0.0

    def cat_count(self, category):
        if category in self.document_in_category:
            return float(self.document_in_category[category])
        return 0.0

    def total_count(self):
        return sum(self.document_in_category.values())

    def categories(self):
        return self.document_in_category.keys()

    def train(self, item, category):
        features = self.get_features(item)
        for feature in features:
            self.incf(feature, category)

        self.incc(category)

    def f_prob(self, feature, category):
        if self.cat_count(category) == 0:
            return 0

        return self.f_count(feature, category) / self.cat_count(category)

    def weighted_prob(self, feature, category, prf, weight=1.0, ap=0.5):
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

    def classify(self, item, default=None):
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


class NaiveBayes(Classifier):
    def doc_prob(self, item, category):
        features = self.get_features(item)

        p = 1
        for feature in features:
            p *= self.weighted_prob(feature, category, self.f_prob)
        return p

    def prob(self, item, category):
        cat_prob = self.cat_count(category) / self.total_count()
        doc_prob = self.doc_prob(item, category)
        return doc_prob * cat_prob


def sample_train(classifier):
    classifier.train('Nobody owns the water.', 'good')
    classifier.train('the quick rabbit jumps fences', 'good')
    classifier.train('buy pharmaceuticals now', 'bad')
    classifier.train('make quick money at the online casino', 'bad')
    classifier.train('the quick brown fox jumps', 'good')
