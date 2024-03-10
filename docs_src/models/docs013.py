from typing import Optional

import databases
import ormar
import sqlalchemy

DATABASE_URL = "sqlite:///test.db"

ormar_base_config = ormar.OrmarConfig(
    database=databases.Database(DATABASE_URL),
    metadata=sqlalchemy.MetaData(),
)


class Artist(ormar.Model):
    # note that tablename is optional
    # if not provided ormar will user class.__name__.lower()+'s'
    # -> artists in this example
    ormar_config = ormar_base_config.copy()

    id: int = ormar.Integer(primary_key=True)
    first_name: str = ormar.String(max_length=100)
    last_name: str = ormar.String(max_length=100)
    born_year: int = ormar.Integer(name="year")


class Album(ormar.Model):
    ormar_config = ormar_base_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    artist: Optional[Artist] = ormar.ForeignKey(Artist)
