import feedparser
import re

def read(feed, classifier):
    '''
    This is an interactive function that reads an RSS feed in xml file
    form and uses the supplied classifier and user input to make guesses
    and teach the classifier.
    First it parses the xml file, then it gives the best guess, finally
    it asks for user input to train the classifier further.
    '''
    f = feedparser.parse(feed)
    for entry in f['entries']:
        print
        print '_____'
        print 'Title:       ' + entry['title'].encode('utf-8')
        print 'Publisher:   ' + entry['publisher'].encode('utf-8')
        print
        print entry['summary'].encode('utf-8')

        # use a composite of parts of the feed entry as the text. 
        # commented out, because entry_features now uses the whole entry.
        #full_text = '%s\n%s\n%s' % (entry['title'], entry['publisher'], entry['summary'])

        print 'Guess:       ' + str(classifier.classify(entry))

        cl = raw_input('Enter category: ')
        classifier.train(entry, cl)

def entry_features(entry):
    '''
    Splits an RSS item into multiple fields, then constructs
    a dictionary (f) of features that include the title,
    summary, publisher, and even upper case words!
    '''
    splitter = re.compile('\\W*')
    f = {}

    title_words = [s.lower() for s in splitter.split(entry['title'])
            if len(s) > 2 and len(s) < 20]
    for word in title_words:
        f['Title:' + word] = 1

    summary_words = [s.lower() for s in splitter.split(entry['summary'])
            if len(s) > 2 and len(s) < 20]

    upper_case = 0
    for i in xrange(len(summary_words)):
        word = summary_words[i]
        f[word] = 1
        if word.isupper():
            upper_case += 1

            if i < len(summary_words) - 1:
                two_words = ' '.join(summary_words[i:i+1])
                f[two_words] = 1
    f['Publisher:' + entry['publisher']] = 1
    if float(upper_case) / len(summary_words) > 0.3:
        f['UPPERCASE'] = 1

    return f
