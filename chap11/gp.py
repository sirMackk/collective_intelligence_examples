from random import random, randint, choice
from copy import deepcopy
from math import log

class FWrapper(object):
    '''
    This is a wrapper object for a function.
    '''
    def __init__(self, function, child_count, name):
        self.function = function
        self.child_count = child_count
        self.name = name


class Node(object):
    '''
    This is a generic Node object that's the basic building block
    of a tree. It can hold references to all the other node types.
    What's more, it can evaluate itself ie. iterate through
    all of it's children, calling each childnode's evaluate
    function and collecting the results.
    '''
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
    '''
    This is a node that holds simple parameters.
    '''
    def __init__(self, idx):
        self.idx = idx

    def evaluate(self, inp):
        return inp[self.idx]

    def display(self, indent=0):
        print '%sp%d' % (' ' * indent, self.idx)


class ConstNode(object):
    '''
    This is a node that holds a parameter that cannot change.
    '''
    def __init__(self, v):
        self.v = v

    def evaluate(self, inp):
        return self.v

    def display(self, indent=0):
        print '%s%d' % (' ' * indent, self.v)


def is_greater(l):
    '''
    Evaluates where l[0] is greater than l[1].
    '''
    if l[0] > l[1]:
        return 1
    else:
        return 0


def if_func(l):
    '''
    Evaluates a simple if statement, returning one of the arguments.
    '''
    if l[0] > 0:
        return l[1]
    else:
        return l[2]

# Wraps up some simple functions to use in the trees.
# Great example to see how FWrapper actually works.
addw = FWrapper(lambda l: l[0] + l[1], 2, 'add')
subw = FWrapper(lambda l: l[0] - l[1], 2, 'subtract')
mulw = FWrapper(lambda l: l[0] * l[1], 2, 'multiply')
ifw = FWrapper(if_func, 3, 'if')
gtw = FWrapper(is_greater, 2, 'isgreater')

f_list = [addw, mulw, ifw, gtw, subw]


def example_tree():
    '''
    Generates an example tree of nodes, using all the basic functions except mulw.
    '''
    return Node(ifw, [Node(gtw, [ParamNode(0), ConstNode(3)]),
                      Node(addw, [ParamNode(1), ConstNode(5)]),
                      Node(subw, [ParamNode(1), ConstNode(2)])])


def make_random_tree(pc, max_depth=4, fpr=0.5, ppr=0.6):
    '''
    Creates a random tree by calling itself recursively. The nodes are created
    totally randomly.
    '''
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
    '''
    The hidden function that's used to generate an example set of data.
    '''
    return x ** 2 + 2 * y + 3 * x + 5


def build_hidden_set():
    '''
    Builds a hidden set of data in order to try out a genetic algorithm
    approach.
    '''
    rows = []
    for i in xrange(200):
        x = randint(0, 40)
        y = randint(0, 40)
        rows.append([x, y, hidden_function(x, y)])

    return rows


def score_function(tree, s):
    '''
    A simple scoring function that compares features with results and
    calculates the difference. The higher the difference, the higher/worse
    the score. The closer a tree to the correct function, the lower
    the difference.
    '''
    diff = 0
    for data in s:
        v = tree.evaluate([data[0], data[1]])
        diff += abs(v - data[2])

    return diff


def mutate(t, pc, prob_change=0.1):
    '''
    Mutates a node by substituting it with a random tree OR
    recursively tries to mutate each child of the node t.
    '''
    if random() < prob_change:
        return make_random_tree(pc)
    else:
        result = deepcopy(t)
        if isinstance(t, Node):
            result.children = [mutate(c, pc, prob_change) for c in t.children]

        return result


def crossover(t1, t2, prob_swap=0.7, top=1):
    '''
    Combines two nodes, t1 and t2, by traversing down each tree and randomly
    stopping at a node in each one. Then it swaps these nodes along with
    their children.
    '''
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
    '''
    Creates a population of random trees, scores them against each other,
    then mutates and crossovers the top trees until the lowest score
    is reached.
    '''
    def select_index():
        return int(log(random()) / log(pexp))

    population = [make_random_tree(pc) for i in xrange(pop_size)]

    for i in xrange(max_gen):
        scores = rank_function(population)
        print scores[0][0]
        if scores[0][0] == 0:
            print 'score!'
            break

        # picks out two of the best trees and discards the rest
        new_pop = [scores[0][1], scores[1][1]]

        # rebuilds the population
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
    '''
    Returns a ranking function as an object.
    '''
    def rank_function(population):
        scores = [(score_function(t, dataset), t) for t in population]
        scores.sort()
        return scores

    return rank_function


def grid_game(p):
    max = (3, 3)
    last_move = [-1, -1]
    location = [[randint(0, max[0]), randint(0, max[1])]]

    location.append([(location[0][0] + 2) % 4, (location[0][1] + 2) % 4])

    for o in xrange(50):
        for i in xrange(2):
            locs = location[i][:] + location[1-i][:]
            locs.append(last_move[i])
            move = p[i].evaluate(locs) % 4

            if last_move[i] == move:
                return 1 - i
            last_move[i] = move
            if move == 0:
                location[i][0] -= 1
                if location[i][0] < 0:
                    location[i][0] = 0
            if move == 1:
                location[i][0] += 1
                if location[i][0] > max[0]:
                    location[i][0] = max[0]
            if move == 2:
                location[i][1] -= 1
                if location[i][1] < 0:
                    location[i][1] = 0
            if move == 3:
                location[i][1] += 1
                if location[i][1] > max[1]:
                    location[i][1] = max[1]
            if location[i] == location[1-i]:
                return i
    return -1


def tournament(pl):
    losses = [0 for p in pl]

    for i in xrange(len(pl)):
        for j in xrange(len(pl)):
            if i == j:
                continue
            winner = grid_game([pl[i], pl[j]])

            if winner == 0:
                losses[j] += 2
            elif winner == 1:
                losses[i] += 2
            elif winner == -1:
                losses[i] += 1
                losses[j] += 1
                pass
    z = zip(losses, pl)
    z.sort()
    return z


class HumanPlayer(object):
    def evaluate(self, board):

        me = tuple(board[0:2])
        others = [tuple(board[x:x+2]) for x in xrange(2, len(board) - 1, 2)]

        for i in xrange(4):
            for j in xrange(4):
                if (i, j) == me:
                    print '0',
                elif (i, j) in others:
                    print 'X',
                else:
                    print '.',
            print

        print 'Your last move was %d' % board[len(board) - 1]
        print ' 0'
        print '2 3'
        print ' 1'
        print 'Enter move: ',

        move = int(raw_input())
        return move
