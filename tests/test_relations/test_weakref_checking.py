import databases
import ormar
import sqlalchemy

from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class Band(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename="bands",
        metadata=metadata,
        database=database,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Artist(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename="artists",
        metadata=metadata,
        database=database,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)

    band: Band = ormar.ForeignKey(Band)


def test_weakref_init():
    band = Band(name="Band")
    artist1 = Artist(name="Artist 1", band=band)
    Artist(name="Artist 2", band=band)
    artist3 = Artist(name="Artist 3", band=band)

    del artist1
    Artist(
        name="Artist 2", band=band
    )  # Force it to check for weakly-referenced objects
    del artist3

    band.artists  # Force it to clean

    assert len(band.artists) == 1
    assert band.artists[0].name == "Artist 2"
