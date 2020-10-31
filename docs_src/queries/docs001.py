from typing import Optional

import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Album(ormar.Model):
    class Meta:
        tablename = "album"
        metadata = metadata
        database = database

    id = ormar.Integer(primary_key=True)
    name = ormar.String(max_length=100)


class Track(ormar.Model):
    class Meta:
        tablename = "track"
        metadata = metadata
        database = database

    id = ormar.Integer(primary_key=True)
    album= ormar.ForeignKey(Album)
    title = ormar.String(max_length=100)
    position = ormar.Integer()