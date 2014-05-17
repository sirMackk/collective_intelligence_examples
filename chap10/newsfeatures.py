import feedparser
import re

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
            
