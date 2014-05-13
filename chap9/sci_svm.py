# coding: utf-8
from sklearn import svm
import random
import advancedclassify

num = advancedclassify.load_numerical()
train, test = [], []
scaled, scaling_f = advancedclassify.scale_data(num)

for item in scaled:
    if random.random() < 0.05:
        test.append(item)
    else:
        train.append(item)

train_X, train_y = [i.data for i in train], [i.match for i in train]
test_X, test_y = [i.data for i in test], [i.match for i in test]

clf = svm.SVC()
clf.fit(train_X, train_y)
print "SVM score on validation data: %.2f" % clf.score(test_X, test_y)
# predict for two people where one doesn't want children
print "If only one wants a child: %d" % clf.predict([scaling_f([28.0, -1, -1, 26.0, -1, 1, 2, 0.8])])[0]
print "(Should be 0)"
# predict for two people where both want children
print "If both want children: %d" % clf.predict([scaling_f([28.0, -1, 1, 26.0, -1, 1, 2, 0.8])])[0]
print "(Should be 1)"
