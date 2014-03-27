from scipy import stats as sp

critics = {'Lisa Rose':
            {'Lady in the Water': 2.5, 'Snakes on a Plane': 3.5,
                'Just My Luck': 3.0, 'Superman Returns': 3.5,
                'You, Me and Dupree': 2.5, 'The Night Listener': 3.0},
            'Gene Seymour':
                {'Lady in the Water': 3.0, 'Snakes on a Plane': 3.5,
                    'Just My Luck': 1.5, 'Superman Returns': 5.0,
                    'The Night Listener': 3.0, 'You, Me and Dupree': 3.5},
            'Michael Phillips':
                {'Lady in the Water': 2.5, 'Snakes on a Plane': 3.0,
                    'Superman Returns': 3.5, 'The Night Listener': 4.0},
            'Caludia Puid':
                {'Snakes on a Plane': 3.5, 'Just My Luck': 3.0,
                    'The Night Listener': 4.5, 'Superman Returns': 4.0,
                    'You, Me and Dupree': 2.5},
            'Mick LaSalle':
                {'Lady in the Water': 3.0, 'Snakes on a Plane': 4.0,
                    'Just My Luck': 2.0, 'Superman Returns': 3.0,
                    'The Night Listener': 3.0, 'You, Me and Dupree': 2.0},
            'Jack Matthews':
                {'Lady in the Water': 3.0, 'Snakes on a Plane': 4.0,
                    'The Night Listener': 3.0, 'Superman Returns': 5.0,
                    'You, Me and Dupree': 3.5},
            'Toby':
                {'Snakes on a Plane': 4.5, 'You, Me and Dupree': 1.0,
                    'Superman Returns': 4.0}
           }


# euclidean distance between two people
def sim_distance(prefs, person1, person2):
    shared_items = {}
    for item in prefs[person1]:
        if item in prefs[person2]:
            shared_items[item] = 1

    if len(shared_items) == 0:
        return 0

    sum_of_squares = sum([(prefs[person1][item] - prefs[person2][item]) ** 2
                            for item in prefs[person1]
                            if item in prefs[person2]])

    return 1 / (1 + sum_of_squares)


# pearson coefficient
def sim_pearson(prefs, person1, person2):
    shared_items = {}
    for item in prefs[person1]:
        if item in prefs[person2]:
            shared_items[item] = 1

    n = len(shared_items)

    if n == 0:
        return 0

    sum1 = sum([prefs[person1][item] for item in shared_items])
    sum2 = sum([prefs[person2][item] for item in shared_items])

    sum1_sq = sum([prefs[person1][item] ** 2 for item in shared_items])
    sum2_sq = sum([prefs[person2][item] ** 2 for item in shared_items])

    product_sum = sum([prefs[person1][item] * prefs[person2][item]
                   for item in shared_items])

    numerator = product_sum - (sum1 * sum2 / n)
    denominator = ((sum1_sq - sum1 ** 2 / n) *
                   (sum2_sq - sum2 ** 2 / n)) ** 0.5

    return (numerator / denominator)


# pearson coefficient using scipy.stats.pearsonr
def scipy_sim_pearson(prefs, person1, person2):
    shared_items = {item: 1 for item in prefs[person1]
            if item in prefs[person2]}

    if len(shared_items) == 0:
        return 0

    return sp.pearsonr([prefs[person1][item] for item in shared_items],
            [prefs[person2][item] for item in shared_items])[0]


def top_matches(prefs, person, n=5, similarity_fn=scipy_sim_pearson):
    scores = [(similarity_fn(prefs, person, other), other)
                for other in prefs if other != person]
    scores.sort()
    scores.reverse()
    return scores[:n]


def get_recommendations(prefs, person, similarity_fn=scipy_sim_pearson):
    totals = {}
    similarity_sums = {}

    for other_person in prefs:
        if other_person != person:
            similarity = similarity_fn(prefs, person, other_person)

            if similarity > 0:
                for item in prefs[other_person]:
                    if item not in prefs[person] or prefs[person][item] == 0:
                        totals.setdefault(item, 0)
                        totals[item] += prefs[other_person][item] * similarity
                        similarity_sums.setdefault(item, 0)
                        similarity_sums[item] += similarity

    rankings = [(total / similarity_sums[item], item)
            for item, total in totals.items()]

    rankings.sort()
    rankings.reverse()
    return rankings


def get_recommendations_imp(prefs, person, similarity_fn=scipy_sim_pearson):
    others = prefs.copy()
    others.pop(person)
    totals = {}
    similarity_sums = {}

    for other in others:
        similarity = similarity_fn(prefs, person, other)
        if similarity > 0:
            for item in prefs[other]:
                if item not in prefs[person] or prefs[person][item] == 0:
                    totals.setdefault(item, 0)
                    totals[item] += prefs[other][item] * similarity
                    similarity_sums.setdefault(item, 0)
                    similarity_sums[item] += similarity

    return sorted([(total / similarity_sums[item], item)
        for item, total in totals.items()], reverse=True)


def transform_prefs(prefs):
    results = {}
    for person in prefs:
        for item in prefs[person]:
            results.setdefault(item, {})
            results[item][person] = prefs[person][item]

    return results
