from typing import Optional

import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///test.db", force_rollback=True)
metadata = sqlalchemy.MetaData()


class Artist(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
        tablename="artists",
    )

    id: int = ormar.Integer(name="artist_id", primary_key=True)
    first_name: str = ormar.String(name="fname", max_length=100)
    last_name: str = ormar.String(name="lname", max_length=100)
    born_year: int = ormar.Integer(name="year")


class Album(ormar.Model):

    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
        tablename="music_albums",
    )

    id: int = ormar.Integer(name="album_id", primary_key=True)
    name: str = ormar.String(name="album_name", max_length=100)
    artist: Optional[Artist] = ormar.ForeignKey(Artist, name="artist_id")
