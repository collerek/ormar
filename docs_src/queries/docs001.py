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

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Track(ormar.Model):
    class Meta:
        tablename = "track"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    album: Optional[Album] = ormar.ForeignKey(Album)
    title: str = ormar.String(max_length=100)
    position: int = ormar.Integer()
