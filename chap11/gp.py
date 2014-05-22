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


class ParamNode(object):
    def __init__(self, idx):
        self.idx = idx

    def evaluate(self, inp):
        return inp[self.idx]


class ConstNode(object):
    def __init__(self, v):
        self.v = v

    def evaluate(self, inp):
        return self.v


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
