from typing import Optional

import databases
import pytest
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Artist(ormar.Model):
    class Meta:
        tablename = "artists"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Album(ormar.Model):
    class Meta:
        tablename = "albums"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    artist: Optional[Artist] = ormar.ForeignKey(Artist, ondelete='CASCADE')


class Track(ormar.Model):
    class Meta:
        tablename = "tracks"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    album: Optional[Album] = ormar.ForeignKey(Album, ondelete='CASCADE')
    title: str = ormar.String(max_length=100)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    if "sqlite" in DATABASE_URL:
        with engine.connect() as connection:
            connection.execute("PRAGMA foreign_keys = ON;")
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    # metadata.drop_all(engine)


# def test_table_structures():
#     col = Album.Meta.table.columns.get('artist')
#     breakpoint()


@pytest.mark.asyncio
async def test_simple_cascade():
    async with database:
        async with database.transaction(force_rollback=True):
            artist = await Artist(name='Dr Alban').save()
            await Album(name="Jamaica", artist=artist).save()
            await Artist.objects.delete(id=artist.id)
            albums = await Album.objects.all()
            assert len(albums) == 0
