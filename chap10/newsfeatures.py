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
    '''
    Iterate over each character in h and strips anything between < and >.
    '''
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
    '''
    Separates text into a list of lower cased strings.
    '''
    splitter = re.compile('\\W*')
    return [s.lower() for s in splitter.split(text) if len(s) > 3]


def get_article_words(get_text=False):
    '''
    Separates an article into a dict of all words, a list of dicts of 
    words for each article, and a list of titles.
    '''
    all_words = {}
    article_words = []
    article_titles = []
    ec = 0
    texts = []

    for feed in feed_list:
        # iterate over each feed from the list
        f = feedparser.parse(feed)

        # iterate over each entry for each feed
        for e in f.entries:
            # skip entry if it has already been scanned
            if e.title in article_titles:
                continue

            # combine the entry title and contents, stripping it from html
            txt = e.title.encode('utf8') + strip_html(e.description.encode('utf8'))
            # divide the title + content into a list oflower cased words
            if get_text:
                texts.append(txt)
            words = separate_words(txt)
            article_words.append({})
            # add title to list of titles
            article_titles.append(e.title)

            # iterate over each word
            for word in words:
                all_words.setdefault(word, 0)
                # increment word count for a given word
                all_words[word] += 1
                # increment word count for a word
                # under a dict representing an article
                article_words[ec].setdefault(word, 0)
                article_words[ec][word] += 1
            ec += 1

    if get_text:
        return all_words, article_words, article_titles, texts
    else:
        return all_words, article_words, article_titles


def make_matrix(all_w, article_w):
    '''
    Transforms the all words list and the article list of dictionaries
    into a matrix.
    '''
    word_vec = []

    # iterate through all the words and filter out
    # any words that appear less than 3 times or
    # more than 0.6 times all the article words.
    for w, c in all_w.items():
        if c > 3 and c < len(article_w) * 0.6:
            word_vec.append(w)

    # build a 2d list (matrix) where each row represents
    # a single article and each column represents a word.
    l1 = [[(word in f and f[word] or 0)
           for word in word_vec] for f in article_w]

    return l1, word_vec


def show_features(w, h, titles, word_vec, out='features.txt'):
    '''
    Outputs a textfile of a combination of:
    <feature words>
    <titles that relate to the feature words the most>
    '''
    with open(out, 'wb') as f:
        pc, wc = np.shape(h)
        top_patterns = [[] for i in xrange(len(titles))]
        pattern_names = []

        # iterate over the number of patterns
        for i in xrange(pc):
            s_list = []
            for j in xrange(wc):
                # combine features (numbers) and their string counter parts
                s_list.append((h[i, j], word_vec[j]))

            s_list.sort()
            s_list.reverse()

            # create a list of words from feature/string list
            n = [s[1] for s in s_list[0:6]]
            # and write it out
            f.write(str(n) + '\n')
            # and save it as a pattern
            pattern_names.append(n)

            f_list = []

            # combine weights and titles
            for j in xrange(len(titles)):
                f_list.append((w[j, i], titles[j]))
                top_patterns[j].append((w[j, i], i, titles[j]))

            # and get the titles of the three biggest weights
            f_list.sort()
            f_list.reverse()

            # and write out three of them
            for feature in f_list[0:3]:
                f.write(str(feature) + '\n')
            f.write('\n')

    return top_patterns, pattern_names


def show_articles(titles, top_patterns, pattern_names, out='articles.txt'):
    '''
    Combines titles with 3 sets of highest weighted features for that title.
    '''
    with open(out, 'wb') as f:
        # iterate over each title and write it to file
        for j in xrange(len(titles)):
            f.write(titles[j].encode('utf8') + '\n')

            # collect patterns for each title and sort them
            top_patterns[j].sort()
            top_patterns[j].reverse()

            # output top 3 patterns
            for i in xrange(3):
                f.write(str(top_patterns[j][i][0]) + ' ' +
                        str(pattern_names[top_patterns[j][i][1]]) + '\n')

            f.write('\n')
