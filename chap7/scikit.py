import treepredict
from sklearn import tree
from sklearn.feature_extraction import DictVectorizer

data = treepredict.my_data

# transform the data to handle strings
selectors = [d[:-1] for d in data]
predictors = [d[-1] for d in data]

selectors = [dict(enumerate(selector)) for selector in selectors]

vect = DictVectorizer(sparse=False)
X = vect.fit_transform(selectors)

# create the classifier
clf = tree.DecisionTreeClassifier(criterion='entropy')
# train it
clf.fit(X, predictors)

# print the resulting classes, it will help
# to make sense of the output graph
print clf.classes_

# create dot graph file with labels
# then transform this file into a png with
# the following command:
# dot -Tpng output_labeled.dot -o output_labeled.png
with open('output_labeled.dot', 'wb') as f:
    tree.export_graphviz(clf, out_file=f,
            feature_names=vect.get_feature_names())
