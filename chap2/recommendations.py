from scipy import stats as sp
from requests import get
import os.path
import zipfile

# download and extract MovieLens dataset if it's not present
if not os.path.exists('ml-100k/u.item') or not os.path.exists('ml-100k/u.data'):
    zip_download = get('http://files.grouplens.org/datasets/movielens/ml-100k.zip')
    with open('ml-100k.zip', 'wb') as f:
        f.write(zip_download.content)

    with zipfile.ZipFile('ml-100k.zip', 'r') as zip_file:
        zip_file.extract('ml-100k/u.data')
        zip_file.extract('ml-100k/u.item')


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

def shared_items_fn(prefs, person1, person2):
    return {item: 1 for item in prefs[person1] if item in prefs[person2]}


# euclidean distance between two people
def sim_distance(prefs, person1, person2):
    '''
    Calculates euclidean distance between two people
    by comparing their shared item scores.
    '''
    shared_items = shared_items_fn(prefs, person1, person2)

    if len(shared_items) == 0:
        return 0

    sum_of_squares = sum([(prefs[person1][item] - prefs[person2][item]) ** 2
                            for item in prefs[person1]
                            if item in prefs[person2]])

    return 1 / (1 + sum_of_squares)


# pearson coefficient
def sim_pearson(prefs, person1, person2):
    '''
    Calculates the pearson r for two people
    using the shared item scores.
    '''
    shared_items = shared_items_fn(prefs, person1, person2)

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
    '''
    Calculates the pearson r for two people
    using the shared item scores and the
    scipy.stats.pearsonr function for improved
    performance.
    '''
    shared_items = {item: 1 for item in prefs[person1]
            if item in prefs[person2]}

    if len(shared_items) == 0:
        return 0

    return sp.pearsonr([prefs[person1][item] for item in shared_items],
            [prefs[person2][item] for item in shared_items])[0]


def top_matches(prefs, person, n=5, similarity_fn=scipy_sim_pearson):
    '''
    Calculates n top similar matches for person.
    '''
    scores = [(similarity_fn(prefs, person, other), other)
                for other in prefs if other != person]
    scores.sort()
    scores.reverse()
    return scores[:n]


def get_recommendations(prefs, person, similarity_fn=scipy_sim_pearson):
    '''
    Generates an orderded list of similar items for person.
    '''
    totals = {}
    similarity_sums = {}

    for other_person in prefs:
        if other_person != person:
            similarity = similarity_fn(prefs, person, other_person)

            if similarity > 0:
                for item in prefs[other_person]:
                    if item not in prefs[person] or prefs[person][item] == 0:
                        totals.setdefault(item, 0)
                        # accumulate movie score times similarity...
                        totals[item] += prefs[other_person][item] * similarity
                        similarity_sums.setdefault(item, 0)
                        # ... and accumulate the total similarity as well ...
                        similarity_sums[item] += similarity

    # ... so we can normalize the final score here!
    rankings = [(total / similarity_sums[item], item)
            for item, total in totals.items()]

    rankings.sort()
    rankings.reverse()
    return rankings


def transform_prefs(prefs):
    '''
    Transforms user based preferences into item based
    preferences ie. {'User': {'item': 3.5, 'item2': 5.0}}
    is turned into {'item': {'User': 3.5'}, 'item2': 
    {'User': 5.0}. Useful when trying to get similar items
    instead of similar users.
    '''
    results = {}
    for person in prefs:
        for item in prefs[person]:
            results.setdefault(item, {})
            results[item][person] = prefs[person][item]

    return results


def calculate_similar_items(prefs, n=10):
    '''
    Generates a list of items along with n
    top matched similar items and their similarity score.
    '''

    result = {}

    item_prefs = transform_prefs(prefs)
    c = 0
    for item in item_prefs:
        c += 1
        if c % 100 == 0:
            print "%d / %d" % (c, len(item_prefs))

        scores = top_matches(item_prefs, item, n, sim_distance)
        # use sim_distance, because pearsonr will
        # have problems with divide by 0 and introduce nan's
        result[item] = scores
    return result


# recommend items to user
def get_recommended_items(prefs, itemMatch, user):
    '''
    Generates a list of recommended items for a user
    based on user preferences (prefs[user]) as well 
    as a list of similar items.
    '''
    user_ratings = prefs[user]
    scores = {}
    total_similar = {}

    for (item, rating) in user_ratings.items():
        for (similarity, item2) in itemMatch[item]:
            if item2 not in user_ratings:
                scores.setdefault(item2, 0)
                scores[item2] += similarity * rating

                total_similar.setdefault(item2, 0)
                total_similar[item2] += similarity

    rankings = [(score / total_similar[item], item)
            for item, score in scores.items()]

    rankings.sort()
    rankings.reverse()
    return rankings


# MovieLens dataset related functions
def load_movie_lens(path='ml-100k/'):
    '''
    Simple function to read in the MovieLens data
    required to play around with all the other functions.
    '''
    movies = {}
    with open(path + 'u.item') as u_items:
        for line in u_items:
            (id, title) = line.split('|')[0:2]
            movies[id] = title

    prefs = {}

    with open(path + 'u.data') as u_data:
        for line in u_data:
            (user, movie_id, rating, time) = line.split('\t')
            prefs.setdefault(user, {})
            prefs[user][movies[movie_id]] = float(rating)

    return prefs
