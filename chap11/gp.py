from random import random, randint, choice
from copy import deepcopy
from math import log

class FWrapper(object):
    def __init__(self, function, child_count, name):
        self.function = function
        self.child_count = child_count
        self.name = name


class Node(object):
    def __init__(self, fw, children):
        self.function = fw.function
        self.name = fw.name
        self.children = children

    def evaluate(self, inp):
        results = [n.evaluate(inp) for n in self.children]
        return self.function(results)

    def display(self, indent=0):
        print (' ' * indent) + self.name
        for c in self.children:
            c.display(indent+1)


class ParamNode(object):
    def __init__(self, idx):
        self.idx = idx

    def evaluate(self, inp):
        return inp[self.idx]

    def display(self, indent=0):
        print '%sp%d' % (' ' * indent, self.idx)


class ConstNode(object):
    def __init__(self, v):
        self.v = v

    def evaluate(self, inp):
        return self.v

    def display(self, indent=0):
        print '%s%d' % (' ' * indent, self.v)


def is_greater(l):
    if l[0] > l[1]:
        return 1
    else:
        return 0


def if_func(l):
    if l[0] > 0:
        return l[1]
    else:
        return l[2]


addw = FWrapper(lambda l: l[0] + l[1], 2, 'add')
subw = FWrapper(lambda l: l[0] - l[1], 2, 'subtract')
mulw = FWrapper(lambda l: l[0] * l[1], 2, 'multiply')
ifw = FWrapper(if_func, 3, 'if')
gtw = FWrapper(is_greater, 2, 'isgreater')

f_list = [addw, mulw, ifw, gtw, subw]


def example_tree():
    return Node(ifw, [Node(gtw, [ParamNode(0), ConstNode(3)]),
                      Node(addw, [ParamNode(1), ConstNode(5)]),
                      Node(subw, [ParamNode(1), ConstNode(2)])])


def make_random_tree(pc, max_depth=4, fpr=0.5, ppr=0.6):
    if random() < fpr and max_depth > 0:
        f = choice(f_list)
        children = [make_random_tree(pc, max_depth - 1, fpr, ppr)
                for i in xrange(f.child_count)]
        return Node(f, children)
    elif random() < ppr:
        return ParamNode(randint(0, pc-1))
    else:
        return ConstNode(randint(0, 10))


def hidden_function(x, y):
    return x ** 2 + 2 * y + 3 * x + 5


def build_hidden_set():
    rows = []
    for i in xrange(200):
        x = randint(0, 40)
        y = randint(0, 40)
        rows.append([x, y, hidden_function(x, y)])

    return rows


def score_function(tree, s):
    diff = 0
    for data in s:
        v = tree.evaluate([data[0], data[1]])
        diff += abs(v - data[2])

    return diff


def mutate(t, pc, prob_change=0.1):
    if random() < prob_change:
        return make_random_tree(pc)
    else:
        result = deepcopy(t)
        if isinstance(t, Node):
            result.children = [mutate(c, pc, prob_change) for c in t.children]

        return result


def crossover(t1, t2, prob_swap=0.7, top=1):
    if random() < prob_swap and not top:
        return deepcopy(t2)
    else:
        result = deepcopy(t1)
        if isinstance(t1, Node) and isinstance(t2, Node):
            result.children = [crossover(c, choice(t2.children), prob_swap, 0)
                    for c in t1.children]

        return result


def evolve(pc, pop_size, rank_function, max_gen=500, mutation_rate=0.1,
        breeding_rate=0.4, pexp=0.7, pnew=0.05):
    def select_index():
        return int(log(random()) / log(pexp))

    population = [make_random_tree(pc) for i in xrange(pop_size)]

    for i in xrange(max_gen):
        scores = rank_function(population)
        print scores[0][0]
        if scores[0][0] == 0:
            print 'score!'
            break

        new_pop = [scores[0][1], scores[1][1]]

        while len(new_pop) < pop_size:
            if random() > pnew:
                new_pop.append(mutate(
                    crossover(scores[select_index()][1],
                        scores[select_index()][1],
                        prob_swap=breeding_rate),
                    pc, prob_change=mutation_rate))
            else:
                new_pop.append(make_random_tree(pc))

        population = new_pop
    scores[0][1].display()
    return scores[0][1]


def get_rank_function(dataset):
    def rank_function(population):
        scores = [(score_function(t, dataset), t) for t in population]
        scores.sort()
        return scores

    return rank_function
