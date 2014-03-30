import feedparser
import re


def get_word_counts(url):
    '''
    Fetches and parses and RSS feed using a url.
    Returns a tuple with a feed's title and
    a dictionary of word counts.
    '''
    parsed = feedparser.parse(url)

    word_count = {}

    for entry in parsed.entries:
        if 'summary' in entry:
            summary = entry.summary
        else:
            summary = entry.description

        words = get_words(' '.join([entry.title, summary]))
        for word in words:
            word_count.setdefault(word, 0)
            word_count[word] += 1

    return (parsed.feed.title, word_count)


def get_words(html):
    '''
    Uses regular expressions to remove html tags and to split
    the resulting text into single words.
    Returns a list of lower cased words.
    '''
    txt = re.compile(r'<[^>]+').sub('', html)

    words = re.compile(r'[^A-Z^a-z]+').split(txt)

    return [word.lower() for word in words if word != '']


if __name__ == '__main__':
    # turn into callable function for use in interactive python session
    # break down into smaller functions for easier understanding
    ap_count = {}
    word_counts = {}

    # iterate through list of feed urls and collect word count for each feed
    # then iterate throught that collection and assign the blog count for each word
    with open('feedlist.txt', 'rb') as f:
        feed_list_length = len(f)
        for feed_url in f:
            title, word_count = get_word_counts(feed_url)
            word_counts[title] = word_count

            for word, count in word_count.items():
                ap_count.setdefault(word, 0)
                if count > 1:
                    ap_count[word] += 1

    word_list = []

    # iterate through list of word:blog_count and find the fraction of
    # how many times the word appears per all the blogs and if it's
    # between 0.1 and 0.5 then append it to word_list
    for word, blog_count in ap_count.items():
        frac = float(blog_count) / feed_list_length
        if frac > 0.1 and frac < 0.5:
            word_list.append(word)

    # first iterate through the word list and print out the tab separated
    # list of words. Then iterate through the word_list again and if the word
    # is in word_count, output it's count preceeded by a tab
    with open('blogdata2.txt', 'wb') as output:
        output.write('Blog')
        for word in word_list:
            output.write('\t%s' % word)

        output.write('\n')
        for blog, word_count in word_counts.items():
            output.write(blog)
            for word in word_list:
                if word in word_count:
                    output.write('\t%d' % word_count[word])
                else:
                    output.write('\t0')
            output.write('\n')
