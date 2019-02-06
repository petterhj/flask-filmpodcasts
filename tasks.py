# Imports
from re import compile, sub, UNICODE
from requests import get
from flask_rq2 import RQ
from rq import get_current_job

from podcast import parse_feed
from database import Podcast, Episode, EpisodeIndex, IntegrityError
from logger import logger


# RQ
rq = RQ()


# Job: Sync (episodes)
@rq.job
def sync():
    logger.info('Syncing podcast episodes')

    job = get_current_job()

    results = {}
    podcasts = Podcast.select()#.limit(3)

    for i, podcast in enumerate(podcasts, 1):
        logger.info('Parsing feed, %s' % (podcast.name))

        error = None
        synced = 0
        ignored = 0

        try:
            episodes = parse_feed(get(podcast.feed_url).text)
        except Exception as e:
            logger.exception('Could not parse feed %s' % (podcast.feed_url))
            error = str(e)
            episodes = []

        for episode in episodes:
            job.meta['progress'] = ((i / float(len(podcasts))) * 100)
            job.save_meta()

            try:
                # Episode entity
                e = Episode.create(podcast=podcast, **episode)
                synced += 1

                # Document index
                clean_pattern = compile(ur'\W+', UNICODE)
                title = sub(clean_pattern, ' ', e.title)
                description = sub(clean_pattern, ' ', e.description)

                EpisodeIndex.insert({
                    EpisodeIndex.rowid: e.id,
                    EpisodeIndex.title: title.lower(),
                    EpisodeIndex.description: description.lower()
                }).execute()

            except IntegrityError:
                ignored +=1
            except:
                logger.exception('Could not add episode to database')

        logger.info('Done parsing %s, added %d episodes, ignored %d' % (podcast.name, synced, ignored))

        results[podcast.id] = {
            'podcast_name': podcast.name,
            'error': error,
            'synced': synced,
            'ignored': ignored
        }

    return results