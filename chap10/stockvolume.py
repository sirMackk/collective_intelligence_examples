import nmf
import urllib2
import numpy as np

tickers = ['YHOO', 'AVP', 'BIIB', 'BP', 'CL', 'CVX',
           'DNA', 'EXPE', 'GOOG', 'PG', 'XOM', 'AMGN']

shortest = 300
prices = {}
dates = None

for t in tickers:
    #rows = urllib2.urlopen('http://ichart.finance.yahoo.com/table.csv?' + \
                           #'s=%s&d=11&e=26&f=2013&g=d&a=3&b=12&c=2003%t' + \
                           #'&ignore=.csv').readlines()
    url = 'http://ichart.finance.yahoo.com/table.csv?s=%s&d=11&e=26&f=2006&' % t
    print url
    try:
        rows = urllib2.urlopen(url).readlines()
    except urllib2.HTTPError, e:
        print e

    prices[t] = [float(r.split(',')[5]) for r in rows[1:] if r.strip() != '']
    if len(prices[t]) < shortest:
        shortest = len(prices[t])

    if not dates:
        dates = [r.split(',')[0] for r in rows[1:] if r.strip() != '']


l1 = [[prices[tickers[i]][j] for i in xrange(len(tickers))]
        for j in xrange(shortest)]


w, h, _ = nmf.factorize(np.matrix(l1), pc=5)
print h
print w


for i in xrange(np.shape(h)[0]):
    print 'Feature %d: ' % i

    ol = [(h[i, j], tickers[j]) for j in xrange(np.shape(h)[1])]
    ol.sort()
    ol.reverse()
    for j in xrange(12):
        print ol[j]
    print

    porder = [(w[d, i], d) for d in xrange(300)]
    porder.sort()
    porder.reverse()
    print [(p[0], dates[p[1]]) for p in porder[0:3]]
    print

