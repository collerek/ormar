from typing import Optional

import databases
import sqlalchemy

import ormar

database = databases.Database("sqlite:///test.db", force_rollback=True)
metadata = sqlalchemy.MetaData()


# note that you do not have to subclass ModelMeta,
# it's useful for type hints and code completion
class MainMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class Artist(ormar.Model):
    class Meta(MainMeta):
        # note that tablename is optional
        # if not provided ormar will user class.__name__.lower()+'s'
        # -> artists in this example
        pass

    id: int = ormar.Integer(primary_key=True)
    first_name: str = ormar.String(max_length=100)
    last_name: str = ormar.String(max_length=100)
    born_year: int = ormar.Integer(name="year")


class Album(ormar.Model):
    class Meta(MainMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    artist: Optional[Artist] = ormar.ForeignKey(Artist)
