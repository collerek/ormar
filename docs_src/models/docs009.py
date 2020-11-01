from typing import Optional

import databases
import sqlalchemy

import ormar
from .docs010 import Artist  # previous example

database = databases.Database("sqlite:///test.db", force_rollback=True)
metadata = sqlalchemy.MetaData()


class Album(ormar.Model):
    class Meta:
        tablename = "music_albums"
        metadata = metadata
        database = database

    id: int = ormar.Integer(name="album_id", primary_key=True)
    name: str = ormar.String(name="album_name", max_length=100)
    artist: Optional[Artist] = ormar.ForeignKey(Artist, name="artist_id")
