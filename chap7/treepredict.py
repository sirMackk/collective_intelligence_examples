from PIL import Image, ImageDraw

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
    def __init__(self, col=-1, value=None, results=None, tb=None, fb=None):
        self.col = col
        self.value = value
        self.results = results
        # tb and fb are nodes - tb is for true and fb is for false
        self.tb = tb
        self.fb = fb


def divide_set(rows, column, value):
    '''
    Splits a set into two sets using the value as the splitter.
    If the value is a string, it will split the rows into
    [every row with string, every row without it]. If the value
    is a number (float,int), then it will split rows into
    [every row < value, every row >= value].
    '''
    # select the best splitting function, which is a lambda wrapped
    # conditional statement using the supplied value as the splitter:
    # one for numerical data
    # other one for anything else
    split_function = None
    if isinstance(value, int) or isinstance(value, float):
        split_function = lambda row: row[column] >= value
    else:
        split_function = lambda row: row[column] == value

    set_1 = [row for row in rows if split_function(row)]
    set_2 = [row for row in rows if not split_function(row)]

    return (set_1, set_2)


def unique_counts(rows):
    '''
    Uses the last column of my_data to create unique categories
    and maintains the count of items for each category.
    '''
    results = {}
    for row in rows:
        r = row[len(row)-1]
        if r not in results:
            results[r] = 0
        results[r] += 1

    return results


def gini_impurity(rows):
    # Another way of calculating information gain (purity)
    # or entropy (impurting).
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
    # Calculates the entropy using the last column (results)
    # as the information input ie. if results look like this:
    # {'None': 1, 'Basic': 1, 'Premium': 1} they are more
    # homogenic then if they looked like:
    # {'None': 0, 'Baisc': 3, 'Premium': 8}.
    # The more similar the result column in rows, the lower
    # the entropy.
    # Here's a good explanation:
    # https://stackoverflow.com/questions/1859554/what-is-entropy-and-information-gain
    from math import log
    #log2 = lambda x: (log(x) / log(2))
    results = unique_counts(rows)
    ent = 0.0
    for r in results.keys():
        p = float(results[r] / float(len(rows)))
        # replaces books log2 func with stdlib one
        #ent = ent - p*log2(p)
        ent = ent - p * log(p, 2)

    return ent


def build_tree(rows, score_f=entropy):
    '''
    Build a decision tree using recursion. Returns the root node.
    '''
    if len(rows) == 0:
        return DecisionNode()
    current_score = score_f(rows)

    best_gain = 0.0
    best_criteria = None
    best_sets = None

    # selects only data columns, not the results
    column_count = len(rows[0]) - 1

    # iterate through every column
    for col in xrange(0, column_count):
        column_values = {}
        # iterate and create a dictionary of column values,
        # ensuring no duplicates
        for row in rows:
            column_values[row[col]] = 1

        # iterate through the unique column values and
        # divide the dataset (rows) using each unique
        # column value. Then compare the information gain
        # for each two sets and choose the best sets with the
        # highest information gain (lowest entropy?)
        # as the column value with which to split this column.
        for value in column_values.keys():
            (set_1, set_2) = divide_set(rows, col, value)

            p = float(len(set_1)) / float(len(rows))
            # This calculates the weighted average entropy of the
            # current pair of sets. The lower the entropy, the higher
            # the gain. The pair with the lowest entropy (gain > best)
            # is saved.
            # current_score is vanilla plain entropy of the raw data.
            # p * score_f(set_1) is weighted average of the entropy
            # of set_1
            # (1 - p) * score_f(set_2) is the weighted average of the
            # entropy of set_2.
            # Notice that p is the size of set_1 relative to the whole
            # set ie. 0.454 ~= 45% and that (1 - p) is the size of
            # set_2 relative to the whole set.
            gain = current_score - p * score_f(set_1) - (1 - p) * score_f(set_2)
            if gain > best_gain and len(set_1) > 0 and len(set_2) > 0:
                best_gain = gain
                best_criteria = (col, value)
                best_sets = (set_1, set_2)

    # Having found the best branches (set_1, set_2 = 
    # true_branch, false_branch):
    # if their is any gain then return a DecisionNode with
    # set_1 being the true branch and set_2 being the false branch.
    # At the same time, recurisvely inspect these child nodes.
    if best_gain > 0:
        true_branch = build_tree(best_sets[0])
        false_branch = build_tree(best_sets[1])
        return DecisionNode(col=best_criteria[0], value=best_criteria[1],
                tb=true_branch, fb=false_branch)
    else:
        # If there was no gain, return a leaf node.
        return DecisionNode(results=unique_counts(rows))


def print_tree(tree, indent=''):
    '''
    Uses recursing to print a decision tree from top to bottom.
    '''
    if tree.results: 
        print str(tree.results)
    else:
        print str(tree.col) + ':' + str(tree.value)+'? '

        print indent + 'T->',
        print_tree(tree.tb, indent+'    ')
        print indent + 'F->',
        print_tree(tree.fb, indent+'    ')


# Two great examples of recursion.
def get_width(tree):
    '''
    Get the width of the tree in nodes.
    '''
    if not tree.tb and not tree.tb:
        return 1
    return get_width(tree.tb) + get_width(tree.fb)


def get_depth(tree):
    '''
    Get the depth of the tree in nodes.
    '''
    if not tree.tb and not tree.fb:
        return 0
    return max(get_depth(tree.tb), get_depth(tree.fb)) + 1


def draw_node(draw, tree, x, y):
    '''
    Use PIL to create nodes and lines for a decision tree.
    '''
    if not tree.results:
        w1 = get_width(tree.fb) * 100
        w2 = get_width(tree.tb) * 100

        left = x - (w1 + w2) / 2
        right = x + (w1 + w2) /2

        draw.text((x - 20, y - 10), str(tree.col) + ':' + str(tree.value), (0, 0, 0))

        draw.line((x, y, left + w1 / 2, y + 100), fill=(255, 0, 0))
        draw.line((x, y, right - w2 / 2, y + 100), fill=(255, 0, 0))

        draw_node(draw, tree.fb, left + w1 / 2, y + 100)
        draw_node(draw, tree.tb, right - w2 / 2, y + 100)
    else:
        txt = ' \n'.join(['%s:%d' %v for v in tree.results.items()])
        draw.text((x - 20, y), txt, (0, 0, 0))

def draw_tree(tree, jpeg='tree.jpg'):
    w = get_width(tree) * 100
    h = get_depth(tree) * 100 + 120

    img = Image.new('RGB', (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    draw_node(draw, tree, w/2, 20)
    img.save(jpeg, 'JPEG')
    

def classify(observation, tree):
    '''
    Uses recursion to generate
    a result based on the observation and a trained
    decision tree.
    '''
    if tree.results:
        return tree.results
    else:
        v = observation[tree.col]
        branch = None
        # This is analogous to the unique_counts function
        if isinstance(v, int) or isinstance(v, float):
            if v >= tree.value:
                branch = tree.tb
            else:
                branch = tree.fb
        else:
            if v == tree.value:
                branch = tree.tb
            else:
                branch = tree.fb
        return classify(observation, branch)


def prune(tree, min_gain):
    '''
    Remove nodes from a decision tree that don't matter
    much in classifying new observations.
    This prevents overfitting. According to The Book,
    since the algorithm will split sets until there's
    nothing to split, pruning will get rid of nodes
    that shouldn't have been split.
    '''
    if not tree.tb.results:
        prune(tree.tb, min_gain)
    if not tree.fb.results:
        prune(tree.fb, min_gain)

    if tree.tb.results and tree.fb.results:
        tb, fb = [], []
        for v, c in tree.tb.results.items():
            tb += [[v]] * c
        for v, c in tree.fb.results.items():
            fb += [[v]] * c

        delta = entropy(tb + fb) - (entropy(tb) + entropy(fb) / 2)
        if delta < min_gain:
            tree.tb, tree.fb = None, None
            tree.results = unique_counts(tb + fb)


def md_classify(observation, tree):
    '''
    Used to classify observations with missing data.
    According to The Book this classification function
    follows multiple branches and weighs each branch
    score to find out which is the best one.
    '''
    if tree.results:
        return tree.results
    else:
        v = observation[tree.col]
        if not v:
            tr, fr = md_classify(observation, tree.tb), md_classify(observation, tree.fb)
            t_count = sum(tr.values())
            f_count = sum(fr.values())
            tw = float(t_count) / (t_count + f_count)
            fw = float(f_count) / (t_count + f_count)
            results = {}
            for k, v in tr.items():
                results[k] = v * tw
            for k, v in fr.items():
                results[k] = v * fw
            return results
        else:
            if isinstance(v, int) or isinstance(v, float):
                if v >= tree.value:
                    branch = tree.tb
                else:
                    branch = tree.fb
            else:
                if v == tree.value:
                    branch = tree.tb
                else:
                    branch = tree.fb
            return md_classify(observation, branch)


def variance(rows):
    if len(rows) == 0:
        return 0
    data = [float(row[len(row) - 1]) for row in rows]
    mean = sum(data) / len(data)
    variance = sum([(d - mean) ** 2 for d in data]) / len(data)
    return variance
