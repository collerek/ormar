from typing import Optional

import databases
import pytest
import sqlalchemy

import ormar
from ormar import NoMatch
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Album(ormar.Model):
    class Meta:
        tablename = "albums"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True, name="album_id")
    name: str = ormar.String(max_length=100)
    is_best_seller: bool = ormar.Boolean(default=False)


class Writer(ormar.Model):
    class Meta:
        tablename = "writers"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True, name="writer_id")
    name: str = ormar.String(max_length=100)


class Track(ormar.Model):
    class Meta:
        tablename = "tracks"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    album: Optional[Album] = ormar.ForeignKey(Album, name="album_id")
    title: str = ormar.String(max_length=100)
    position: int = ormar.Integer()
    play_count: int = ormar.Integer(nullable=True)
    written_by: Optional[Writer] = ormar.ForeignKey(Writer, name="writer_id")


async def get_sample_data():
    album = await Album(name="Malibu").save()
    writer1 = await Writer.objects.create(name="John")
    writer2 = await Writer.objects.create(name="Sue")
    track1 = await Track(
        album=album, title="The Bird", position=1, play_count=30, written_by=writer1
    ).save()
    track2 = await Track(
        album=album,
        title="Heart don't stand a chance",
        position=2,
        play_count=20,
        written_by=writer2,
    ).save()
    tracks3 = await Track(
        album=album, title="The Waters", position=3, play_count=10, written_by=writer1
    ).save()
    return album, [track1, track2, tracks3]


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_quering_by_reverse_fk():
    async with database:
        async with database.transaction(force_rollback=True):
            sample_data = await get_sample_data()
            track1 = sample_data[1][0]
            album = await Album.objects.first()

            assert await album.tracks.exists()
            assert await album.tracks.count() == 3

            track = await album.tracks.get_or_create(
                title="The Bird", position=1, play_count=30
            )
            assert track == track1
            assert len(album.tracks) == 1

            track = await album.tracks.get_or_create(
                title="The Bird2", position=4, play_count=5
            )
            assert track != track1
            assert track.pk is not None
            assert len(album.tracks) == 2

            await album.tracks.update_or_create(pk=track.pk, play_count=50)
            assert len(album.tracks) == 2
            track = await album.tracks.get_or_create(title="The Bird2")
            assert track.play_count == 50
            assert len(album.tracks) == 1

            await album.tracks.remove(track)
            assert track.album is None
            await track.delete()

            assert len(album.tracks) == 0

            track6 = await album.tracks.update_or_create(
                title="The Bird3", position=4, play_count=5
            )
            assert track6.pk is not None
            assert track6.play_count == 5

            assert len(album.tracks) == 1

            await album.tracks.remove(track6)
            assert track6.album is None
            await track6.delete()

            assert len(album.tracks) == 0


@pytest.mark.asyncio
async def test_getting():
    async with database:
        async with database.transaction(force_rollback=True):
            sample_data = await get_sample_data()
            album = sample_data[0]
            track1 = await album.tracks.fields(["album", "title", "position"]).get(
                title="The Bird"
            )
            track2 = await album.tracks.exclude_fields("play_count").get(
                title="The Bird"
            )
            for track in [track1, track2]:
                assert track.title == "The Bird"
                assert track.album == album
                assert track.play_count is None

            assert len(album.tracks) == 1

            tracks = await album.tracks.all()
            assert len(tracks) == 3

            assert len(album.tracks) == 3

            tracks = await album.tracks.order_by("play_count").all()
            assert len(tracks) == 3
            assert tracks[0].title == "The Waters"
            assert tracks[2].title == "The Bird"

            assert len(album.tracks) == 3

            track = await album.tracks.create(
                title="The Bird Fly Away", position=4, play_count=10
            )
            assert track.title == "The Bird Fly Away"
            assert track.position == 4
            assert track.album == album

            assert len(album.tracks) == 4

            tracks = await album.tracks.all()
            assert len(tracks) == 4

            tracks = await album.tracks.limit(2).all()
            assert len(tracks) == 2

            tracks2 = await album.tracks.limit(2).offset(2).all()
            assert len(tracks2) == 2
            assert tracks != tracks2

            tracks3 = await album.tracks.filter(play_count__lt=15).all()
            assert len(tracks3) == 2

            tracks4 = await album.tracks.exclude(play_count__lt=15).all()
            assert len(tracks4) == 2
            assert tracks3 != tracks4

            assert len(album.tracks) == 2

            await album.tracks.clear()
            tracks = await album.tracks.all()
            assert len(tracks) == 0
            assert len(album.tracks) == 0

            still_tracks = await Track.objects.all()
            assert len(still_tracks) == 4
            for track in still_tracks:
                assert track.album is None


@pytest.mark.asyncio
async def test_cleaning_related():
    async with database:
        async with database.transaction(force_rollback=True):
            sample_data = await get_sample_data()
            album = sample_data[0]
            await album.tracks.clear(keep_reversed=False)
            tracks = await album.tracks.all()
            assert len(tracks) == 0
            assert len(album.tracks) == 0

            no_tracks = await Track.objects.all()
            assert len(no_tracks) == 0


@pytest.mark.asyncio
async def test_loading_related():
    async with database:
        async with database.transaction(force_rollback=True):
            sample_data = await get_sample_data()
            album = sample_data[0]
            tracks = await album.tracks.select_related("written_by").all()
            assert len(tracks) == 3
            assert len(album.tracks) == 3
            for track in tracks:
                assert track.written_by is not None

            tracks = await album.tracks.prefetch_related("written_by").all()
            assert len(tracks) == 3
            assert len(album.tracks) == 3
            for track in tracks:
                assert track.written_by is not None


@pytest.mark.asyncio
async def test_adding_removing():
    async with database:
        async with database.transaction(force_rollback=True):
            sample_data = await get_sample_data()
            album = sample_data[0]
            track_new = await Track(title="Rainbow", position=5, play_count=300).save()
            await album.tracks.add(track_new)
            assert track_new.album == album
            assert len(album.tracks) == 4

            track_check = await Track.objects.get(title="Rainbow")
            assert track_check.album == album

            await album.tracks.remove(track_new)
            assert track_new.album is None
            assert len(album.tracks) == 3

            track1 = album.tracks[0]
            await album.tracks.remove(track1, keep_reversed=False)
            with pytest.raises(NoMatch):
                await track1.load()

            track_test = await Track.objects.get(title="Rainbow")
            assert track_test.album is None
