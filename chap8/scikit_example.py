import numpredict
from sklearn.neighbors import KNeighborsRegressor
import numpy as np


def get_inputs(data):
    return [i['input'] for i in data]


def get_results(data):
    return [i['result'] for i in data]


def get_pair(data):
    return np.array(get_inputs(data)), np.array(get_results(data))


# create two random wine sets
wine_set_1 = numpredict.wine_set_1()
wine_set_2 = numpredict.wine_set_2()

# break these sets into training data and testing data
train1, test1 = numpredict.divide_data(wine_set_1, test=0.07)
train2, test2 = numpredict.divide_data(wine_set_2, test=0.07)

# format the sets into numpy arrays suitable for scikit-learn
train1_X, train1_y = get_pair(train1)
test1_X, test1_y = get_pair(test1)

train2_X, train2_y = get_pair(train2)
test2_X, test2_y = get_pair(train2)

# create two regressors
knn1 = KNeighborsRegressor()
knn2 = KNeighborsRegressor()

# train them using the training sets
knn1.fit(train1_X, train1_y)
knn2.fit(train2_X, train2_y)

# check out their scores
print "Accuracy score for predications made on the first wine set:",
print "%0.2f%%" % (knn1.score(test1_X, test1_y) * 100)
print "Accuracy score for predications made on the second wine set:",
print "%0.2f%%" % (knn2.score(test2_X, test2_y) * 100)
