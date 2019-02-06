#!/usr/bin/python
# -*- coding: utf-8 -*-

# Imports
from re import compile, sub, UNICODE
from peewee import fn, JOIN
from flask import Flask, request, abort, render_template, jsonify, Response

import config
from tasks import rq, sync
from database import Podcast, Episode, EpisodeIndex


# App
app = Flask(__name__)
app.config['RQ_REDIS_URL'] = config.REDIS_URL
app.config['RQ_QUEUES'] = config.REDIS_QUEUES
rq.init_app(app)

scheduler = rq.get_scheduler()
job = sync.cron(config.PODCAST_SYNC_CRON, 'sync-podcasts')


# Index
@app.route('/')
def index():
    # Return
    podcasts = []

    for p in Podcast.select():
        podcast = p.__data__
        podcast.update({'episode_count': p.episode_count})
        podcasts.append(podcast)

    return render_template('index.html', **{
        'podcasts': sorted(podcasts, key=lambda p: p['episode_count'], reverse=True)
        # 'podcasts': podcasts,
    })


# JSON: Status
@app.route('/json/status/')
def status():
    # Jobs
    scheduled_jobs = {job.get_id(): {
        'scheduled_for': time,
        'status': job.get_status(),
        'enqueued_at': job.enqueued_at,
        'started_at': job.started_at,
        'ended_at': job.ended_at,
        'meta': job.meta,
        'result': job.result,
    } for job, time in scheduler.get_jobs(with_times=True)}

    # Database
    database = {
        'podcasts': Podcast.select().count(),
        'episodes': Episode.select().count(),
    }

    return jsonify({
        'scheduler': scheduled_jobs.get('cron-sync-podcasts', {}),
        'database': database,
    })


# JSON: Search episodes
@app.route('/json/search/')
def search_episodes():
    title = request.args.get('title')

    if not title:
        abort(Response('Missing argument: title', 401))

    search_term = title.lower().strip()
    clean_pattern = compile(ur'\W+', UNICODE)
    search_term = sub(clean_pattern, ' ', search_term)
    use_fts = True

    # Query
    if use_fts:
        query = EpisodeIndex.search_lucene(
            search_term,
            weights=[2, 1],
            with_score=True,
            score_alias='search_score'
        )
    else:
        query = Episode.select().where(
            Episode.title.contains(search_term) | 
            Episode.description.contains(search_term)
        ).order_by(Episode.pubdate.desc())

    # Results
    results = []

    for episode in query:
        result = episode
        episode = Episode.get(Episode.id == result.rowid) if use_fts else episode
        podcast = episode.podcast
        episode = episode.__data__

        if use_fts:
            score = result.search_score
        else:
            score = 1 if search_term in episode['title'].lower() and search_term in episode['description'].lower() else 2        

        episode.update({
            'podcast_name': podcast.name, 
            'podcast_color': podcast.color,
            'score': score
        })
        results.append(episode)

    results = sorted(results, key=lambda k: k['score']) 

    return jsonify({'results': results})


# JSON: Podcasts
@app.route('/json/podcasts/')
def podcasts():
    podcasts = {}

    for p in Podcast.select():
        podcast = p.__data__
        podcast.update({'episode_count': p.episode_count})

        podcasts[p.id] = podcast

    return jsonify(podcasts)


# JSON: Episodes
@app.route('/json/podcasts/episodes/')
def episodes():
    episodes = []

    for e in Episode.select().order_by(Episode.pubdate.desc()).limit(40):
        podcast = e.podcast
        episode = e.__data__
        episode.update({
            'podcast_name': podcast.name, 
            'podcast_color': podcast.color
        })
        # podcast.update({'episode_count': p.episode_count})
        episodes.append(episode)
        # episodes[p.id] = episode

    return jsonify(episodes)