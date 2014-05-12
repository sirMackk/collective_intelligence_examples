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
