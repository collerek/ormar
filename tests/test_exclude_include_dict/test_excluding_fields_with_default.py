import random
from typing import Optional

import databases
import ormar
import pytest
import sqlalchemy

from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


def get_position() -> int:
    return random.randint(1, 10)


class Album(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename="albums",
        metadata=metadata,
        database=database,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    is_best_seller: bool = ormar.Boolean(default=False, nullable=True)


class Track(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename="tracks",
        metadata=metadata,
        database=database,
    )

    id: int = ormar.Integer(primary_key=True)
    album: Optional[Album] = ormar.ForeignKey(Album)
    title: str = ormar.String(max_length=100)
    position: int = ormar.Integer(default=get_position)
    play_count: int = ormar.Integer(nullable=True, default=0)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_excluding_field_with_default():
    async with database:
        async with database.transaction(force_rollback=True):
            album = await Album.objects.create(name="Miami")
            await Track.objects.create(title="Vice City", album=album, play_count=10)
            await Track.objects.create(title="Beach Sand", album=album, play_count=20)
            await Track.objects.create(title="Night Lights", album=album)

            album = await Album.objects.fields("name").get()
            assert album.is_best_seller is None

            album = await Album.objects.exclude_fields({"is_best_seller", "id"}).get()
            assert album.is_best_seller is None

            album = await Album.objects.exclude_fields({"is_best_seller": ...}).get()
            assert album.is_best_seller is None

            tracks = await Track.objects.all()
            for track in tracks:
                assert track.play_count is not None
                assert track.position is not None

            album = (
                await Album.objects.select_related("tracks")
                .exclude_fields({"is_best_seller": ..., "tracks": {"play_count"}})
                .get(name="Miami")
            )
            assert album.is_best_seller is None
            assert len(album.tracks) == 3
            for track in album.tracks:
                assert track.play_count is None
                assert track.position is not None

            album = (
                await Album.objects.select_related("tracks")
                .exclude_fields(
                    {
                        "is_best_seller": ...,
                        "tracks": {"play_count": ..., "position": ...},
                    }
                )
                .get(name="Miami")
            )
            assert album.is_best_seller is None
            assert len(album.tracks) == 3
            for track in album.tracks:
                assert track.play_count is None
                assert track.position is None

            album = (
                await Album.objects.select_related("tracks")
                .exclude_fields(
                    {"is_best_seller": ..., "tracks": {"play_count", "position"}}
                )
                .get(name="Miami")
            )
            assert album.is_best_seller is None
            assert len(album.tracks) == 3
            for track in album.tracks:
                assert track.play_count is None
                assert track.position is None
