from typing import Optional

import databases
import ormar
import sqlalchemy

DATABASE_URL = "sqlite:///test.db"

ormar_base_config = ormar.OrmarConfig(
    database=databases.Database(DATABASE_URL), metadata=sqlalchemy.MetaData()
)


class Album(ormar.Model):
    ormar_config = ormar_base_config.copy(tablename="album")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Track(ormar.Model):
    ormar_config = ormar_base_config.copy(tablename="track")

    id: int = ormar.Integer(primary_key=True)
    album: Optional[Album] = ormar.ForeignKey(Album)
    title: str = ormar.String(max_length=100)
    position: int = ormar.Integer()
