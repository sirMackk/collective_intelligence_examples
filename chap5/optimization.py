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
    '''
    Cost function for the flights problem.
    '''
    total_price = 0
    latest_arrival = 0
    earliest_dep = 24 * 60

    # iterate through the solution and the people list in pairs
    # ie (x1, x2, y1, y2, etc)
    for d in xrange(len(sol) / 2):
        # select a person's origin airport
        origin = people[d][1]
        # and setup the inbound/outbound flights
        outbound = flights[(origin, destination)][int(sol[d])]
        return_flight = flights[(destination, origin)][int(sol[d+1])]
        # sum up the inbound/outbound prices
        total_price += outbound[2]
        total_price += return_flight[2]
        # set up the latest and earliest arrivals ie.
        # if the current person is earlier than the earliest
        # he becomes the earliest.
        if latest_arrival < get_minutes(outbound[1]):
            latest_arrival = get_minutes(outbound[1])
        if earliest_dep > get_minutes(return_flight[0]):
            earliest_dep = get_minutes(return_flight[0])

    # use the same loop as above in order to figure out the total waiting time
    # and apply costs to this waiting time
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
    '''
    Random optimization function. It picks 10000 random solutions,
    calculates their cost using costf, and keeps the solution with
    the lowest cost.
    '''
    best = 999999999
    best_r = None
    for i in xrange(10000):
        # generate random solution
        r = [random.randint(domain[i][0], domain[i][1])
                for i in xrange(len(domain))]

        cost = costf(r)
        # if the cost is lower than the current best cost
        # set the current best cost to the new cost and set
        # the current best solution to the new solution.
        if cost < best:
            best = cost
            best_r = r

    return best_r


def hill_climb(domain, costf):
    '''
    Optimize a cost using the hill climb algorithm. 
    https://en.wikipedia.org/wiki/Hill_climbing
    '''
    # start by randomly creating a solution
    sol = [random.randint(domain[i][0], domain[i][1])
            for i in xrange(len(domain))]

    # loop until the solution has stopped changing ie. until
    # the hill climb has found a local optimum.
    while 1:
        # set up an empty list of neighboring solutions for the initial one
        neighbors = []
        for j in xrange(len(domain)):
            # if the specific input j is larger than domain[j][0] (0 in this
            # case), then append the current solution set to the neighbors 
            # list, but increase the element j by 1.
            if sol[j] > domain[j][0]:
                neighbors.append(sol[0:j] + [sol[j]+1] + sol[j+1:])
            # as above - except if sol[j] is smaller than the domain element,
            # append the current solution but decrease the element j by 1
            if sol[j] < domain[j][1]:
                neighbors.append(sol[0:j] + [sol[j]-1] + sol[j+1:])

        current = costf(sol)
        best = current
        # iterate over all of the neighbors and if one of them is
        # better (lower cost) then the current best solution,
        # make that neighbor the current solution.
        for j in xrange(len(neighbors)):
            cost = costf(neighbors[j])
            if cost < best:
                best = cost
                sol = neighbors[j]

        if best == current:
            # if best and current stop changing, the local optimum has been
            # achieved.
            break

    print best
    return sol


def annealing_optimize(domain, costf, T=10000.0, cool=0.95, step=1):
    '''
    Optimization function that works by simulated annealing.
    https://en.wikipedia.org/wiki/Simulated_annealing
    '''
    # create a random initial solution
    vec = [float(random.randint(domain[i][0], domain[i][1]))
            for i in xrange(len(domain))]

    while T > 0.1:
        # choose a random number, which will later choose
        # a specific input from the input solution.
        i = random.randint(0, len(domain) - 1)
        # choose a random integer between -step and step
        # that will change the randomly chosen specific
        # input
        dir = random.randint(-step, step)

        # python way of copying a list
        vec_b = vec[:]
        vec_b[i] += dir
        # ensure that the value of vec_b[i] is within the domain
        # ie is between 0 and 8
        if vec_b[i] < domain[i][0]:
            vec_b[i] = domain[i][0]
        elif vec_b[i] > domain[i][1]:
            vec_b[i] = domain[i][1]

        # calculate the cost of the initial solution
        # and the cost of the newly found solution
        ea = costf(vec)
        eb = costf(vec_b)
        # calculate the probability of accepting
        # a higher cost solution (worse). As the temperature (T) drops,
        # the probabilty also drops. As the process progresses, it becomes
        # less and less likely that a worse solution is chosen, so this
        # algorithm "zeros in" on the best solution. This probability
        # will be higher at the start of the process.
        p = pow(math.e, (-eb-ea) / T)

        # if the new solution is better than the current one or if
        # the probability is high enough, accept the new solution
        # as the current solution.
        if (eb < ea or random.random() < p):
            vec = vec_b

        # decrease the temperature.
        T = T * cool
    return vec


def genetic_optimize(domain, costf, pop_size=50, step=1,
        mut_prob=0.2, elite=0.2, max_iter=100):
    '''
    Use a genetic algorithm to find a solution.
    https://en.wikipedia.org/wiki/Genetic_algorithm
    '''
    def mutate(vec):
        '''
        Randomly increase or decrease a random element of a vector by step.
        '''
        i = random.randint(0, len(domain) - 1)
        if random.random() < 0.5 and vec[i] > domain[i][0]:
            return vec[0:i] + [vec[i]-step] + vec[i+1:]
        # this sometimes doesnt hit and so returns None
        #elif vec[i] < domain[i][1]:
        else:
            return vec[0:i] + [vec[i]+step] + vec[i+1:]

    def crossover(r1, r2):
        '''
        Randomly combine a part of r1 and r2 into one vector.
        '''
        i = random.randint(1, len(domain) - 2)
        return r1[0:i] + r2[i:]

    # setup a population list.
    pop = []
    # and populate it with pop_size number of random solutions
    for i in xrange(pop_size):
        vec = [random.randint(domain[i][0], domain[i][1])
            for i in xrange(len(domain))]
        pop.append(vec)

    # choose an integer representing the number of "elite"
    # solutions.
    top_elite = int(elite*pop_size)

    for i in xrange(max_iter):
        # gather all the costs for the current population and sort them
        scores = [(costf(v), v) for v in pop]
        scores.sort()
        # use the scores to rank the solutions and create a list
        # of sorted solutions
        ranked = [v for (s, v) in scores]

        # work with only the elite portion of the population, ie
        # cut the population (pop) down the elite, then mutate/
        # crossover them until the new population reaches the max
        # population limit.
        pop = ranked[0:top_elite]

        while len(pop) < pop_size:
            # randomly choose to either mutate or crossover each
            # element of the population.
            if random.random() < mut_prob:
                # mutate a random elite solution and append it 
                # to the population.
                c = random.randint(0, top_elite)
                pop.append(mutate(ranked[c]))
            else:
                # crossover two random solutions from the elite 
                # solutions
                c1 = random.randint(0, top_elite)
                c2 = random.randint(0, top_elite)
                pop.append(crossover(ranked[c1], ranked[c2]))
        # print the best solution score for this generation
        print scores[0][0]

    return scores[0][1]
