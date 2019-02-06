#!/usr/bin/python
# -*- coding: utf-8 -*-


# Imports
from re import sub
from dateutil import parser
from bs4 import BeautifulSoup

from logger import logger


# Parse feed
def parse_feed(feed_data):
    '''
    Returns list of parsed episode by feed data (xml).
    '''

    data = BeautifulSoup(feed_data, 'html.parser')

    logger.info('Parsing feed data, length=%d' % (len(feed_data)))

    items = data.findAll('item')

    logger.info('Found %d items' % (len(items)))

    episodes = []

    for item in items:
        title = clean(item.find('title').text)
        # title = unicode(title, 'utf-8')

        description = item.find('description') or item.find('itunes:summary')
        description = description.text if description else ''
        description = clean(BeautifulSoup(description, 'lxml').get_text())
        # description = unicode(description, 'utf-8')

        pubdate = parser.parse(item.find('pubdate').text.strip())

        episodes.append({
            'title': title,
            'description': description,
            'pubdate': pubdate,
        })

    logger.info('Returning %d parsed items' % (len(episodes)))

    return episodes


# Clean
def clean(string):
    REMOVE_WORDS = ['Direct Download']
    REPALCE_WORDS = [[u'\u2013', '-'], [u'\u2014', '-'], [u'\u2018', '"'], [u'\u2019', '\''], [u'\u201c', '\''], [u'\u201d', '"']]
    string = string.strip()

    for word in REPALCE_WORDS:
        string = sub(word[0], word[1], string)

    for word in REMOVE_WORDS:
        string = string.replace(word, '')

    string = sub(r'(\.|\-|\,|\:|\)|[0-9])([A-Z])', '\g<1> \g<2>', string)

    return string




if __name__ == '__main__':
    from requests import get
    from json import dumps
    # episodes = parse('http://feeds.feedburner.com/filmjunk')
    # episodes = parse('http://www.whmpodcast.com/feeds/posts/default?alt=rss')
    # episodes = parse_feed('http://feeds.feedburner.com/filmcast')
    # episodes = parse_feed('http://directorsclubpodcast.libsyn.com/rss')
    feed_data = get('http://feeds.frogpants.com/filmsack_feed.xml').text
    episodes = parse_feed(feed_data)

    print '~'*100
    for episode in episodes[0:3]:
        print '-'*10
        print episode.get('title'), type(episode.get('title'))
        print episode.get('description'), type(episode.get('description'))
        print episode.get('pubdate')
        print '='*100