import feedparser
import re
import numpy as np

feed_list = ['http://today.reuters.com/rss/topNews',
            'http:/today.reuters.com/rss/domesticNews',
            'http://today.reuters.com/rss/worldNews',
            'http://hosted.ap.org/lineups/TOPHEADS-rss_2.0.xml',
            'http://hosted.ap.org/lineups/USHEADS-rss_2.0.xml',
            'http://hosted.ap.org/lineups/WORLDHEADS-rss_2.0.xml',
            'http://hosted.ap.org/lineups/POLITICSHEADS-rss_2.0.xml',
            'http://www.nytimes.com/services/xml/rss/nyt/HomePage.xml',
            'http://www.nytimes.com/services/xml/rss/nyt/International.xml',
            'http://news.google.com/?output=rss',
            'http://www.foxnews.com/xmlfeed/rss/0,4313,0,00.rss',
            'http://www.foxnews.com/xmlfeed/rss/0,4313,80,00.rss',
            'http://www.foxnews.com/xmlfeed/rss/0,4313,81,00.rss',
            'http://rss.cnn.com/rss/edition.rss',
            'http://rss.cnn.com/rss/edition_world.rss',
            'http://rss.cnn.com/rss/edition_us.rss']


def strip_html(h):
    p = ''
    s = 0
    for c in h:
        if c == '<':
            s = 1
        elif c == '>':
            s = 0
            p += ' '
        elif s == 0:
            p += c
    return p


def separate_words(text):
    splitter = re.compile('\\W*')
    return [s.lower() for s in splitter.split(text) if len(s) > 3]


def get_article_words():
    all_words = {}
    article_words = []
    article_titles = []
    ec = 0

    for feed in feed_list:
        f = feedparser.parse(feed)

        for e in f.entries:
            if e.title in article_titles:
                continue

            txt = e.title.encode('utf8') + strip_html(e.description.encode('utf8'))
            words = separate_words(txt)
            article_words.append({})
            article_titles.append(e.title)

            for word in words:
                all_words.setdefault(word, 0)
                all_words[word] += 1
                article_words[ec].setdefault(word, 0)
                article_words[ec][word] += 1
            ec += 1

    return all_words, article_words, article_titles


def make_matrix(all_w, article_w):
    word_vec = []

    for w, c in all_w.items():
        if c > 3 and c < len(article_w) * 0.6:
            word_vec.append(w)

    l1 = [[(word in f and f[word] or 0)
           for word in word_vec] for f in article_w]

    return l1, word_vec


def show_features(w, h, titles, word_vec, out='features.txt'):
    with open(out, 'wb') as f:
        pc, wc = np.shape(h)
        top_patterns = [[] for i in xrange(len(titles))]
        pattern_names = []

        for i in xrange(pc):
            s_list = []
            for j in xrange(wc):
                s_list.append((h[i, j], word_vec[j]))

            s_list.sort()
            s_list.reverse()

            n = [s[1] for s in s_list[0:6]]
            f.write(str(n) + '\n')
            pattern_names.append(n)

            f_list = []

            for j in xrange(len(titles)):
                f_list.append((w[j, i], titles[j]))
                top_patterns[j].append((w[j, i], i, titles[j]))

            f_list.sort()
            f_list.reverse()

            for feature in f_list[0:3]:
                f.write(str(feature) + '\n')
            f.write('\n')

    return top_patterns, pattern_names


def show_articles(titles, top_patterns, pattern_names, out='articles.txt'):
    with open(out, 'wb') as f:
        for j in xrange(len(titles)):
            f.write(titles[j].encode('utf8') + '\n')

            top_patterns[j].sort()
            top_patterns[j].reverse()

            for i in xrange(3):
                f.write(str(top_patterns[j][i][0]) + ' ' +
                        str(pattern_names[top_patterns[j][i][1]]) + '\n')

            f.write('\n')
