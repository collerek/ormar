import ormar
import sqlalchemy
from ormar import DatabaseConnection

DATABASE_URl = "sqlite+aiosqlite:///models_docs010.db"

database = DatabaseConnection(DATABASE_URl, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Child(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
        tablename="children",
    )

    id: int = ormar.Integer(name="child_id", primary_key=True)
    first_name: str = ormar.String(name="fname", max_length=100)
    last_name: str = ormar.String(name="lname", max_length=100)
    born_year: int = ormar.Integer(name="year_born", nullable=True)


class ArtistChildren(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
        tablename="children_x_artists",
    )


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
    children = ormar.ManyToMany(Child, through=ArtistChildren)
