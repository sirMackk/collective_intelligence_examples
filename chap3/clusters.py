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
        self.desitance = distance
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


def print_clust(clust, labels=None, n=0):
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
