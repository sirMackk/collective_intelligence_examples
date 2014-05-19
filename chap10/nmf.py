import numpy as np


def diff_cost(a, b):
    '''
    Calculates the difference of two arrays.
    '''
    diff = 0
    for i in xrange(np.shape(a)[0]):
        for j in xrange(np.shape(a)[1]):
            diff += pow(a[i, j] - b[i, j], 2)

    return diff


def factorize(v, pc=10, iter=50):
    '''
    NMF algorithm magick.
    '''
    # filter all 0 rows to avoid NaN errors
    idx_mask, _ = np.nonzero(v.sum(axis=1) > 0)
    v = v[idx_mask][0]

    ic = np.shape(v)[0]
    fc = np.shape(v)[1]

    w = np.matrix([[np.random.random() for j in xrange(pc)] for i in xrange(ic)])
    h = np.matrix([[np.random.random() for i in xrange(fc)] for i in xrange(pc)])

    for i in xrange(iter):
        wh = w * h
        cost = diff_cost(v, wh)

        if i % 10 == 0:
            print cost

        if cost == 0:
            break

        hn = np.transpose(w) * v
        hd = np.transpose(w) * w * h

        h = np.matrix(np.array(h) * np.array(hn) / np.array(hd))

        wn = v * np.transpose(h)
        wd = w * h * np.transpose(h)

        w = np.matrix(np.array(w) * np.array(wn) / np.array(wd))

    return w, h, idx_mask
