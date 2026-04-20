# type: ignore
import pytest

import ormar
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Song(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="songs")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_equality():
    async with base_ormar_config.database:
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
    async with base_ormar_config.database:
        song1 = await Song.objects.create(name="Song")
        prev_hash = hash(song1)

        await song1.update(name="Song 2")
        assert hash(song1) == prev_hash


@pytest.mark.asyncio
async def test_hash_changes_with_fields_if_no_pk():
    async with base_ormar_config.database:
        song1 = Song(name="Song")
        prev_hash = hash(song1)

        song1.name = "Song 2"
        assert hash(song1) != prev_hash
