from random import random, randint
import math


def wine_price(rating, age):
    peak_age = rating - 50

    price = rating / 2
    if age > peak_age:
        price = price * (5 - (age - peak_age) / 2)
    else:
        price = price * (5 * ((age + 1) / peak_age))
    if price < 0:
        price = 0
    return price


def wine_set_1():
    rows = []
    for i in xrange(300):
        rating = random() * 50 + 50
        age = random() * 50

        price = wine_price(rating, age)
        price *= (random() * 0.2 + 0.9)

        rows.append({'input': (rating, age), 'result': price})

    return rows


def wine_set_2():
    rows = []
    for i in xrange(300):
        rating = random() * 50 + 50
        age = random() * 50
        aisle = float(randint(1, 20))
        bottle_size = [375.0, 750.0, 1500.0, 3000.0][randint(0, 3)]
        price = wine_price(rating, age)
        price *= bottle_size / 750
        price *= (random() * 0.2 + 0.9)
        rows.append({'input': (rating, age, aisle, bottle_size),
            'result': price})

    return rows


def euclidean(v1, v2):
    d = 0.0
    for i in xrange(len(v1)):
        d += (v1[i] - v2[i]) ** 2
    return math.sqrt(d)


def get_distances(data, vec1):
    distance_list = []
    for i in xrange(len(data)):
        vec2 = data[i]['input']
        distance_list.append((euclidean(vec1, vec2), i))
    distance_list.sort()
    return distance_list


def knn_estimate(data, vec1, k=3):
    d_list = get_distances(data, vec1)
    avg = 0.0

    for i in xrange(k):
        idx = d_list[i][1]
        avg += data[idx]['result']
    avg = avg / k
    return avg


def inverse_weight(dist, num=1.0, const=0.1):
    return num / (dist + const)


def subtract_weight(dist, const=1.0):
    if dist > const:
        return 0
    else:
        return const-dist


def gaussian(dist, sigma=10.0):
    return math.e ** (-dist ** 2 / (2 * sigma ** 2))


def weighted_knn(data, vec1, k=5, weight_f=gaussian):
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
    train_set = []
    test_set = []
    for row in data:
        if random() < test:
            test_set.append(row)
        else:
            train_set.append(row)

    return train_set, test_set


def test_algorithm(algf, train_set, test_set):
    error = 0.0
    # iterate over each train_set (0.05) and calculate
    # the guess, then compare it with the actual data
    # and return the square of the difference.
    for row in test_set:
        guess = algf(train_set, row['input'])
        error += (row['result'] - guess) ** 2

    return error / len(test_set)


def cross_validate(algf, data, trials=100, test=0.05):
    # perform cross validation on data
    error = 0.0
    # iterate trials number of times over data, taking
    # random test_sets and running them through an algorithm
    # and sum up the errors.
    for i in xrange(trials):
        train_set, test_set = divide_data(data, test)
        error += test_algorithm(algf, train_set, test_set)

    return error / trials


def rescale(data, scale):
    scaled_data = []
    for row in data:
        scaled = [scale[i] * row['input'][i] for i in xrange(len(scale))]
        scaled_data.append({'input': scaled, 'result': row['result']})
    return scaled_data


def create_cost_function(algf, data):
    def cost_f(scale):
        s_data = rescale(data, scale)
        return cross_validate(algf, s_data, trials=10)
    return cost_f
