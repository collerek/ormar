import databases
import ormar
import sqlalchemy

from .docs008 import Child

database = databases.Database("sqlite:///test.db", force_rollback=True)
metadata = sqlalchemy.MetaData()


class ArtistChildren(ormar.Model):
    class Meta:
        tablename = "children_x_artists"
        metadata = metadata
        database = database


class Artist(ormar.Model):
    class Meta:
        tablename = "artists"
        metadata = metadata
        database = database

    id: int = ormar.Integer(name="artist_id", primary_key=True)
    first_name: str = ormar.String(name="fname", max_length=100)
    last_name: str = ormar.String(name="lname", max_length=100)
    born_year: int = ormar.Integer(name="year")
    children = ormar.ManyToMany(Child, through=ArtistChildren)
