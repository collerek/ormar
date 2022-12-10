# type: ignore
import databases
import pytest
import sqlalchemy

import ormar
from ormar import ModelDefinitionError, property_field
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Song(ormar.Model):
    class Meta:
        tablename = "songs"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_equality():
    async with database:
        song1 = await Song.objects.create(name="Song")
        song2 = await Song.objects.create(name="Song")
        song3 = Song(name="Song")
        song4 = Song(name="Song")

        assert song1 == song1
        assert song3 == song4

        assert song1 != song2
        assert song1 != song3
        assert song3 != song1
        assert song1 is not None


@pytest.mark.asyncio
async def test_hash_doesnt_change_with_fields_if_pk():
    async with database:
        song1 = await Song.objects.create(name="Song")
        prev_hash = hash(song1)

        await song1.update(name="Song 2")
        assert hash(song1) == prev_hash


@pytest.mark.asyncio
async def test_hash_changes_with_fields_if_no_pk():
    async with database:
        song1 = Song(name="Song")
        prev_hash = hash(song1)

        song1.name = "Song 2"
        assert hash(song1) != prev_hash
