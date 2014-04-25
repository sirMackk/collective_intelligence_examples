
my_data=[['slashdot', 'USA', 'yes', 18, 'None'],
        ['google', 'France', 'yes', 23, 'Premium'],
        ['digg', 'USA', 'yes', 24, 'Basic'],
        ['kiwitobes', 'France', 'yes', 23, 'Basic'],
        ['google', 'UK', 'no', 21, 'Premium'],
        ['(direct)', 'New Zealand', 'no', 12, 'None'],
        ['(direct)', 'UK', 'no', 21, 'Basic'],
        ['google', 'USA', 'no', 24, 'Premium'],
        ['slashdot', 'France', 'yes', 19, 'None'],
        ['digg', 'USA', 'no', 18, 'None'],
        ['google', 'UK', 'no', 18, 'None'],
        ['kiwitobes', 'UK', 'no', 19, 'None'],
        ['digg', 'New Zealand', 'yes', 12, 'Basic'],
        ['slashdot', 'UK', 'no', 21, 'None'],
        ['google', 'UK', 'yes', 18, 'Basic'],
        ['kiwitobes', 'France', 'yes', 19, 'Basic']]


class DecisionNode(object):
    def _init__(self, col=-1, value=None, results=None, tb=None, fb=None):
        self.col = col
        self.value = value
        self.results = results
        # tb and fb are nodes - tb is for true and fb is for false
        self.tb = tb
        self.fb = fb


def divide_set(rows, column, value):
    # splits a set into two sets using a chosen split_function
    split_function = None
    if isinstance(value, int) or isinstance(value, float):
        split_function = lambda row: row[column] >= value
    else:
        split_function = lambda row: row[column] == value

    set_1 = [row for row in rows if split_function(row)]
    set_2 = [row for row in rows if not split_function(row)]

    return (set_1, set_2)


def unique_counts(rows):
    # calculates how mixed a set is
    results = {}
    for row in rows:
        r = row[len(row)-1]
        if r not in results:
            results[r] = 0
        results[r] += 1

    return results


def gini_impurity(rows):
    # calculates the chance for every row, that a row
    # would be randomly assigned to the wrong outcome.
    # the higher the p, the worse the split.
    total = len(rows)
    counts = unique_counts(rows)
    imp = 0
    for k1 in counts:
        p1 = float(counts[k1]) / total
        for k2 in counts:
            if k1 == k2:
                continue
            p2 = float(counts[k2]) / total
            imp += p1 * p2

    return imp


def entropy(rows):
    # check the entropy of a set (how much disorder there is).
    # TODO: check if log2 can be substituted with something from
    # the stdlib.
    from math import log
    log2 = lambda x: log(x) / log(2)
    results = unique_counts(rows)
    ent = 0.0
    for r in results.keys():
        p = float(results[r] / len(rows))
        ent = ent - p*log2(p)

    return ent


def build_tree(rows, score_f=entropy):
    if len(rows) == 0:
        return DecisionNode()
    current_score = score_f(rows)

    best_gain = 0.0
    best_criteria = None
    best_sets = None

    column_count = len(rows[0]) - 1

    for col in xrange(0, column_count):
        column_values = {}
        for row in rows:
            column_values[row[col]] = 1

        for value in column_values.keys():
            (set_1, set_2) = divide_set(rows, col, value)

        p = float(len(set_1)) / float(len(rows))
        gain = current_score - p * score_f(set_1) - (1 - p) * score_f(set_2)
        if gain > best_gain and len(set_1) > 0 and len(set_2) > 0:
            best_gain = gain
            best_criteria = (col, value)
            best_sets = (set_1, set_2)

    if best_gain > 0:
        true_branch = build_tree(best_sets[0])
        false_branch = build_tree(best_sets[1])
        return DecisionNode(col=best_criteria[0], value=best_criteria[1],
                tb=true_branch, fb=false_branch)
    else:
        return DecisionNode(results=unique_counts(rows))
