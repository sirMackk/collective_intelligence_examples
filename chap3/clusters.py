from PIL import Image, ImageDraw
import random

def read_file(file_name):
    '''
    Read a tab delimited file of frequent words on blogs.
    Row 1 are words, Column 1 are blog names.
    '''
    with open(file_name, 'rb') as f:
        lines = f.readlines()

    col_names = lines[0].strip().split('\t')[1:]

    row_names = []
    data = []

    for line in lines[1:]:
        row = line.strip().split('\t')
        # append blog name
        row_names.append(row[0])
        data.append([float(i) for i in row[1:]])

    return (row_names, col_names, data)


def pearson(v1, v2):
    '''
    Calculate the pearson r for two sets of values.
    Return 1.0 - pearson r in order to "create a smaller
    distance between items that are more similar", ie.
    the smaller the value, the closer two items are.
    '''
    sum1 = sum(v1)
    sum2 = sum(v2)

    sum1_square = sum([v ** 2 for v in v1])
    sum2_square = sum([v ** 2 for v in v2])

    product_sum = sum([v1[i] * v2[i] for i in xrange(len(v1))])

    numerator = product_sum - (sum1 * sum2 / len(v1))
    denominator = ((sum1_square - sum1 ** 2 / len(v1)) ** 0.5
                  * (sum2_square - sum2 ** 2 / len(v1)))

    if denominator == 0:
        return 0

    return 1.0 - (numerator / denominator)


class Bicluster(object):
    def __init__(self, vector, left=None, right=None, distance=0.0, id=None):
        self.left = left
        self.right = right
        self.vector = vector
        self.distance = distance
        self.id = id


def hcluster(rows, distance=pearson):
    '''
    Uses rows of data to create a tree of nodes, which represent
    clustered data.
    '''
    distances = {}
    current_clust_id = -1

    # create a list of Bicluster nodes representing every row
    clust = [Bicluster(rows[i], id=i) for i in xrange(len(rows))]

    while len(clust) > 1:
        lowest_pair = (0, 1)
        closest = distance(clust[0].vector, clust[1].vector)

        # compare every pair to every other pair
        for i in xrange(len(clust)):
            for j in xrange(i + 1, len(clust)):
                # check if distance is in distances and if not - 
                # calculate it and add it.
                if (clust[i].id, clust[j].id) not in distances:
                    distances[(clust[i].id, clust[j].id)] = distance(
                            clust[i].vector, clust[j].vector)

                d = distances[(clust[i].id, clust[j].id)]

                if d < closest:
                    closest = d
                    lowest_pair = (i, j)

        # calculate average of the lower_pair of clusters ie.
        # add the lowest pair rows column by column and divide by 2.0
        # each time.
        merged_vectors = [
            (clust[lowest_pair[0]].vector[i] + clust[lowest_pair[1]].vector[i]) / 2.0
            for i in xrange(len(clust[0].vector))]

        # use averaged pair of clusters and treat it as the parent node
        # of the lowest pair of nodes:
        # Create new parent cluster and attach the lowest_pair to its
        # left and right branches and assign the current_clust_id so
        # that these parent-nodes have negative ids whereas the end-leaf nodes
        # have positive id.
        new_cluster = Bicluster(merged_vectors, left=clust[lowest_pair[0]],
                                right=clust[lowest_pair[1]],
                                distance=closest, id=current_clust_id)

        # update the current_clust_id
        current_clust_id -= 1
        # delete the lowest_pair from the clust list, since they've
        # been successfully processed
        del clust[lowest_pair[1]]
        del clust[lowest_pair[0]]

        # add parent-node cluster to cluster list to be processed
        clust.append(new_cluster)

    # return the root node
    return clust[0]


def kcluster(rows, distance=pearson, k=4):
    # collects the min and max for a given row
    ranges = [(min([row[i] for row in rows]), max([row[i] for row in rows]))
            for i in xrange(len(rows[0]))]

    # creates k randomly placed centroids
    clusters = [[random.random() * (ranges[i][1] - ranges[i][0]) + ranges[i][0]
        for i in xrange(len(rows[0]))] for j in xrange(k)]

    last_matches = None

    for t in xrange(1000):
        print 'Iteration %d' % t
        best_matches = [[] for i in xrange(k)]

        # iterate over each row
        for j in xrange(len(rows)):
            row = rows[j]
            best_match = 0
            # iterate over each cluster
            for i in xrange(k):
                d = distance(clusters[i], row)
                # find the cluster closest to a row
                if d < distance(clusters[best_match], row):
                    best_match = i
                # append the best matched row index to specific cluster 
                # in list of clusters
                best_matches[best_match].append(j)

        if best_matches == last_matches:
            break
        last_matches = best_matches

        # iterate through the clusters again
        for i in xrange(k):
            # create list with 0.0s the size of the no. of columns
            avgs = [0.0] * len(rows[0])
            if len(best_matches[i]) > 0:
                # iterate through a k cluster
                for row_id in best_matches[i]:
                    # iterate through a row's using the id
                    # in the cluster
                    for m in xrange(len(rows[row_id])):
                        # and accumulate column by column.
                        # essentially, we're summing up the columns
                        # of each cluster. 
                        avgs[m] += rows[row_id][m]
                # iterate through the avgs
                for j in xrange(len(avgs)):
                    # divide each average by the length
                    # of each cluster
                    avgs[j] /= len(best_matches[i])
                # overwrite each centroid with the updated averages
                clusters[i] = avgs
    return best_matches


def print_clust(clust, labels=None, n=0):
    '''
    Print a simple representation of the clustered data.
    '''
    for i in xrange(n):
        print ' ',
    if clust.id < 0:
        print '-'
    else:
        if not labels:
            print clust.id
        else:
            print labels[clust.id]

    if clust.left:
        print_clust(clust.left, labels=labels, n=n+1)
    if clust.right:
        print_clust(clust.right, labels=labels, n=n+1)


def get_height(clust):
    if not clust.left and not clust.right:
        return 1

    # recursive yay!
    return get_height(clust.left) + get_height(clust.right)


def get_depth(clust):
    if not clust.left and not clust.right:
        return 0

    return max(get_depth(clust.left), get_depth(clust.right)) + clust.distance


def draw_node(draw, clust, x, y, scaling, labels):
    if clust.id < 0:
        h1 = get_height(clust.left) * 20
        h2 = get_height(clust.right) * 20

        top = y - (h1 + h2) / 2
        bottom = y + (h1 + h2) / 2

        line_length = clust.distance * scaling

        draw.line((x, top+h1 / 2, x, bottom - h2 / 2), fill=(255, 0, 0))

        draw.line((x, top + h1 / 2, x + line_length, top + h1 / 2),
                fill=(255, 0, 0))

        draw.line((x, bottom - h2 / 2, x + line_length, bottom - h2 / 2),
                fill=(255, 0, 0))

        draw_node(draw, clust.left, x + line_length, top + h1 / 2, scaling,
                labels)
        draw_node(draw, clust.right, x + line_length, bottom - h2 / 2, scaling,
                labels)
    else:
        draw.text((x + 5, y - 7), labels[clust.id], (0, 0, 0))


def draw_dendrogram(clust, labels, jpeg='clusters.jpg'):
    height = get_height(clust) * 20
    width = 1200
    depth = get_depth(clust)

    scaling = float(width - 150) / depth

    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    draw.line((0, height / 2, 10, height / 2), fill=(255, 0, 0))

    draw_node(draw, clust, 10, (height / 2), scaling, labels)
    img.save(jpeg, 'JPEG')

