#!/usr/bin/python
# -*- coding: utf-8 -*-


# Imports
from os import path
from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel, RowIDField, SearchField
# from playhouse.sqliteq import SqliteQueueDatabase
from playhouse.hybrid import hybrid_property

import config


# Database
db = SqliteExtDatabase(config.DATABASE_FILE, **{
    'pragmas': {
        'journal_mode': 'off',
    #     'cache_size': 10000,  # 10000 pages, or ~40MB
    #     'foreign_keys': 1,  # Enforce foreign-key constraints
    },
    # 'check_same_thread': False
})


# Model: Base
class BaseModel(Model):
    class Meta:
        database = db


# Model: Podcast
class Podcast(BaseModel):
    name = CharField(max_length=50)
    short_name = CharField(max_length=3, unique=True)
    feed_url = CharField(max_length=125, unique=True)
    color = CharField(max_length=6, unique=True)

    @hybrid_property
    def episode_count(self):
        return self.episodes.count()


# Model: Episode
class Episode(BaseModel):
    podcast = ForeignKeyField(Podcast, backref='episodes')
    title = CharField()
    description = TextField()
    pubdate = DateTimeField()

    class Meta:
         indexes = (
            (('podcast', 'title', 'pubdate'), True),
        )


# Model: EpisodeIndex
class EpisodeIndex(FTSModel):
    # Full-text search index.
    rowid = RowIDField()
    title = SearchField()
    description = SearchField()

    class Meta:
        database = db
        options = {'tokenize': 'porter'}


# Connect
db.connect()


if __name__ == '__main__':
    db.create_tables([Podcast, Episode, EpisodeIndex])
    
    p1 = {
        'name': 'Film Junk Podcast', 
        'short_name': 'fjp', 
        'feed_url': 'http://feeds.feedburner.com/filmjunk',
        'color': '00C3E2'
    }
    Podcast.create(**p1)