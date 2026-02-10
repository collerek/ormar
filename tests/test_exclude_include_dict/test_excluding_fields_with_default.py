import random
from typing import Optional

import ormar
import pytest

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


def get_position() -> int:
    return random.randint(1, 10)


class Album(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="albums")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    is_best_seller: Optional[bool] = ormar.Boolean(default=False, nullable=True)


class Track(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="tracks")

    id: int = ormar.Integer(primary_key=True)
    album: Optional[Album] = ormar.ForeignKey(Album)
    title: str = ormar.String(max_length=100)
    position: int = ormar.Integer(default=get_position)
    play_count: Optional[int] = ormar.Integer(nullable=True, default=0)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_excluding_field_with_default():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
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
