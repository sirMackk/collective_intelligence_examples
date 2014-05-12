import gzip


class MatchRow(object):
    def __init__(self, row, all_num=False):
        if all_num:
            self.data = [float(row[i]) for i in xrange(len(row) - 1)]
        else:
            self.data = row[0:len(row) - 1]
        self.match = int(row[len(row) - 1])


def load_match(filename, all_num=False):
    rows = []
    with gzip.open(filename, 'r') as f:
        for line in f:
            rows.append(MatchRow(line.split(','), all_num))

    return rows


def linear_train(rows):
    averages = {}
    counts = {}

    for row in rows:
        klass = row.match

        averages.setdefault(klass, [0.0] * (len(row.data)))
        counts.setdefault(klass, 0)

        for i in xrange(len(row.data)):
            averages[klass][i] += float(row.data[i])

        counts[klass] += 1

    for klass, avg in averages.items():
        for i in xrange(len(avg)):
            avg[i] /= counts[klass]

    return averages


def dot_product(v1, v2):
    return sum([v1[i] * v2[i] for i in xrange(len(v1))])


def dp_classify(point, avgs):
    b = (dot_product(avgs[1], avgs[1]) - dot_product(avgs[0], avgs[0])) / 2
    y = dot_product(point, avgs[0]) - dot_product(point, avgs[1]) + b
    if y > 0:
        return 0
    else:
        return 1


def yes_no(v):
    if v == 'yes':
        return 1
    elif v == 'no':
        return -1
    else:
        return 0


def match_count(interest1, interest2):
    l1 = interest1.split(':')
    l2 = interest2.split(':')
    x = 0
    for v in l1:
        if v in l2:
            x += 1

    return x


def miles_distance(a1, a2):
    return 0


def load_numerical():
    old_rows = load_match('matchmaker.gz')
    new_rows = []
    for row in old_rows:
        d = row.data
        data = [float(d[0]), yes_no(d[1]), yes_no(d[2]), float(d[5]),
                yes_no(d[6]), yes_no(d[7]), match_count(d[3], d[8]),
                miles_distance(d[4], d[9]), row.match]
        new_rows.append(MatchRow(data))
    return new_rows


def scale_data(rows):
    low = [99999999.0] * len(rows[0].data)
    high = [-999999999.0] * len(rows[0].data)

    for row in rows:
        d = row.data
        print d
        for i in xrange(len(d)):
            if d[i] < low[i]:
                low[i] = d[i]
            if d[i] > high[i]:
                high[i] = d[i]
        print high[i], low[i]
        print high, low

    def scale_input(d):
        return [(d[i] - low[i]) / (high[i] - low[i])
                for i in xrange(len(low))]

    new_rows = [MatchRow(scale_input(row.data) + [row.match])
                for row in rows]

    return new_rows, scale_input
