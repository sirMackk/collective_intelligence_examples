import time
import random
import math

people = [('Seymour', 'BOS'),
        ('Franny', 'DAL'),
        ('Zooey', 'CAK'),
        ('Walt', 'MIA'),
        ('Buddy', 'ORD'),
        ('Les', 'OMA')]

destination = 'LGA'

flights = {}

with open('schedule.txt', 'rb') as f:
    for line in f.readlines():
        origin, dest, depart, arrive, price = line.strip().split(',')
        flights.setdefault((origin, dest), [])

        flights[(origin, dest)].append((depart, arrive, int(price)))


def get_minutes(t):
    x = time.strptime(t, '%H:%M')
    return x[3] * 60 + x[4]


def print_schedule(r):
    for d in xrange(len(r) / 2):
        name = people[d][0]
        origin = people[d][1]
        out = flights[(origin, destination)][r[d]]
        ret = flights[(destination, origin)][r[d+1]]

        print '%10s%10s %5s-%5s $%3s %5s-%5s $%3s' % (name, origin,
                                                    out[0], out[1], out[2],
                                                    ret[0], ret[1], ret[2])

def schedule_cost(sol):
    total_price = 0
    latest_arrival = 0
    earliest_dep = 24 * 60

    for d in xrange(len(sol) / 2):
        origin = people[d][1]
        outbound = flights[(origin, destination)][int(sol[d])]
        return_flight = flights[(destination, origin)][int(sol[d+1])]

        total_price += outbound[2]
        total_price += return_flight[2]

        if latest_arrival < get_minutes(outbound[1]):
            latest_arrival = get_minutes(outbound[1])
        if earliest_dep > get_minutes(return_flight[0]):
            earliest_dep = get_minutes(return_flight[0])

    total_wait = 0
    for d in xrange(len(sol) / 2):
        origin = people[d][1]
        outbound = flights[(origin, destination)][int(sol[d])]
        return_flight = flights[(destination, origin)][int(sol[d+1])]
        total_wait += latest_arrival - get_minutes(outbound[1])
        total_wait += get_minutes(return_flight[0]) - earliest_dep

    if latest_arrival > earliest_dep:
        total_price += 50

    return total_price + total_wait


def random_optimize(domain, costf):
    best = 999999999
    best_r = None
    for i in xrange(10000):
        r = [random.randint(domain[i][0], domain[i][1])
                for i in xrange(len(domain))]

        cost = costf(r)

        if cost < best:
            best = cost
            best_r = r

    print costf(best_r)
    return best_r


def hill_climb(domain, costf):
    sol = [random.randint(domain[i][0], domain[i][1])
            for i in xrange(len(domain))]

    while 1:
        neighbors = []
        for j in xrange(len(domain)):

            if sol[j] > domain[j][0]:
                neighbors.append(sol[0:j] + [sol[j]+1] + sol[j+1:])
            if sol[j] < domain[j][1]:
                neighbors.append(sol[0:j] + [sol[j]-1] + sol[j+1:])

        current = costf(sol)
        best = current
        for j in xrange(len(neighbors)):
            cost = costf(neighbors[j])
            if cost < best:
                best = cost
                sol = neighbors[j]

        if best == current:
            break

    print best
    return sol
