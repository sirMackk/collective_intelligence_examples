from sklearn import decomposition
from sklearn.feature_extraction import text
import pickle
import gzip

dataset = {}
for fname in ['titles', 'texts']:
    with gzip.open('%s.gz' % fname, 'rb') as f:
        dataset[fname] = pickle.load(f)


vectorizer = text.CountVectorizer(max_df=0.95, max_features=320)
counts = vectorizer.fit_transform(dataset['texts'])
tfidf = text.TfidfTransformer().fit_transform(counts)

nmf = decomposition.NMF(n_components=10).fit(tfidf)
feature_names = vectorizer.get_feature_names()
print len(feature_names)

for topic_idx, topic in enumerate(nmf.components_):
    print "Topic #%d:" % topic_idx
    print " ".join([feature_names[i]
    for i in topic.argsort()[:-21:-1]])
    print


