from random import random, randint
import math
import numpy as np
import matplotlib.pyplot as plt


def wine_price(rating, age):
    '''
    Returns a wine's price based on rating and age.
    '''
    peak_age = rating - 50

    price = rating / 2
    if age > peak_age:
        price = price * (5 - (age - peak_age))
    else:
        price = price * (5 * ((age + 1) / peak_age))
    if price < 0:
        price = 0
    return price


def wine_set_1():
    '''
    Creates a simple set of 300 wines that is composed of
    a tuple (rating, age) and the price.
    '''
    rows = []
    for i in xrange(300):
        rating = random() * 50 + 50
        age = random() * 50

        price = wine_price(rating, age)
        price *= (random() * 0.4 + 0.8)

        rows.append({'input': (rating, age), 'result': price})

    return rows


def wine_set_2():
    '''
    Creates a set of 300 wines with a tuple of features:
    (rating, age aisle, and bottle size.
    '''
    rows = []
    for i in xrange(300):
        rating = random() * 50 + 50
        age = random() * 50
        aisle = float(randint(1, 20))
        bottle_size = [375.0, 750.0, 1500.0, 3000.0][randint(0, 3)]
        price = wine_price(rating, age)
        price *= (bottle_size / 750)
        price *= (random() * 0.9 + 0.2)
        rows.append({'input': (rating, age, aisle, bottle_size),
            'result': price})

    return rows


def wine_set_3():
    '''
    Creates a set of 300 wines based on the wine_set_1
    function, except that each wine has a 50% chance
    of being discounted.
    '''
    rows = wine_set_1()
    for row in rows:
        if random() < 0.5:
            row['result'] *= 0.6
    return rows


def euclidean(v1, v2):
    '''
    Computes the euclidean distance between two vectors.
    '''
    d = 0.0
    for i in xrange(len(v1)):
        d += (v1[i] - v2[i]) ** 2
    return math.sqrt(d)


def get_distances(data, vec1):
    '''
    Calculates the distances between vec1 and all the other
    vectors from data. Returns a SORTED list with the closest
    data points first.
    '''
    distance_list = []
    for i in xrange(len(data)):
        vec2 = data[i]['input']
        distance_list.append((euclidean(vec1, vec2), i))
    distance_list.sort()
    return distance_list


def knn_estimate(data, vec1, k=3):
    '''
    Estimates the average price of k nearest neighbors.
    '''
    d_list = get_distances(data, vec1)
    avg = 0.0

    for i in xrange(k):
        idx = d_list[i][1]
        avg += data[idx]['result']
    avg = avg / k
    return avg


def inverse_weight(dist, num=1.0, const=0.1):
    '''
    Uses an inverse function to return a normalized
    value.
    '''
    return num / (dist + const)


def subtract_weight(dist, const=1.0):
    if dist > const:
        return 0
    else:
        return const-dist


def gaussian(dist, sigma=10.0):
    '''
    Uses gaussian function to return a normalized
    value.
    '''
    return math.e ** (-dist ** 2 / (2 * sigma ** 2))


def weighted_knn(data, vec1, k=5, weight_f=gaussian):
    '''
    Uses weights to normalize the average of k nearest neighbors.
    Useful for when neighbor distance isn't a smooth function.
    '''
    d_list = get_distances(data, vec1)
    avg = 0.0
    total_weight = 0.0

    for i in xrange(k):
        dist = d_list[i][0]
        idx = d_list[i][1]
        weight = weight_f(dist)
        avg += weight * data[idx]['result']
        total_weight += weight
    avg = avg / total_weight
    #avg /= total_weight

    return avg


def divide_data(data, test=0.05):
    '''
    Divides a data set into a training set and a test set.
    The training set trains a classifier and then this classifier
    is judged against the test set to see how accurate the classifier
    is.
    '''
    train_set = []
    test_set = []
    for row in data:
        if random() < test:
            test_set.append(row)
        else:
            train_set.append(row)

    return train_set, test_set


def test_algorithm(algf, train_set, test_set):
    '''
    This checks how accurate the classifier (algf)
    is. It iterates through each test set example
    , uses algf to make a guess and then sums
    the square of the errors.
    '''
    error = 0.0
    # iterate over each train_set (0.05) and calculate
    # the guess, then compare it with the actual data
    # and return the square of the difference.
    for row in test_set:
        guess = algf(train_set, row['input'])
        error += (row['result'] - guess) ** 2

    return error / len(test_set)


def cross_validate(algf, data, trials=100, test=0.05):
    '''
    Performs trials number of runs on a data set using
    algf as the algorithm. For each trial, the set is
    randomly divided into a training set and a test set,
    then the algorithm is trained. Following that, the
    errors are summed and the average is returned.
    '''
    error = 0.0
    # iterate trials number of times over data, taking
    # random test_sets and running them through an algorithm
    # and sum up the errors.
    for i in xrange(trials):
        train_set, test_set = divide_data(data, test)
        error += test_algorithm(algf, train_set, test_set)

    return error / trials


def rescale(data, scale):
    '''
    Data is reset in scale ie. normalized to get rid of
    issues with highly different data.
    '''
    scaled_data = []
    for row in data:
        scaled = [scale[i] * row['input'][i] for i in xrange(len(scale))]
        scaled_data.append({'input': scaled, 'result': row['result']})
    return scaled_data


def create_cost_function(algf, data):
    '''
    Uses cross validation to create a cost function.
    '''
    def cost_f(scale):
        s_data = rescale(data, scale)
        return cross_validate(algf, s_data, trials=10)
    return cost_f


# Domain to work with 4 features - wine_set_2
weight_domain = [(0, 20)] * 4


def prob_guess(data, vec1, low, high, k=5, weight_f=gaussian):
    '''
    Creates a probability curve for k nearest neighbors ie.
    judges how probably vec1's neighbor is.
    '''
    d_list = get_distances(data, vec1)
    n_weight = 0.0
    t_weight = 0.0

    for i in xrange(k):
        dist = d_list[i][0]
        idx = d_list[i][1]
        weight = weight_f(dist)
        v = data[idx]['result']

        if v >= low and v <= high:
            n_weight += weight
        t_weight += weight

    if t_weight == 0:
        return 0

    return n_weight / t_weight


def cumulative_graph(data, vec1, high, k=5, weight_f=gaussian):
    # numpredict.cumulative_graph(data, (99, 10), 120)
    t1 = np.arange(0.0, high, 0.1)
    cprob = np.array([prob_guess(data, vec1, 0, v, k, weight_f) for v in t1])
    plt.plot(t1, cprob)
    plt.show()


def probability_graph(data, vec1, high, k=5, weight_f=gaussian, ss=5.0):
    # numpredict.probability_graph(data, (99, 10), 120)
    t1 = np.arange(0.0, high, 0.1)
    probs = [prob_guess(data, vec1, v, v+0.1, k, weight_f) for v in t1]
    smoothed = []
    for i in xrange(len(probs)):
        sv = 0.0
        for j in xrange(0, len(probs)):
            dist = abs(i-j) * 0.1
            weight = gaussian(dist, sigma=ss)
            sv += weight * probs[j]
        smoothed.append(sv)
    smoothed = np.array(smoothed)

    plt.plot(t1, smoothed)
    plt.show()
