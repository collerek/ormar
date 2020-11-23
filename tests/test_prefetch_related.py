from typing import List, Optional

import databases
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Tonation(ormar.Model):
    class Meta:
        tablename = "tonations"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Shop(ormar.Model):
    class Meta:
        tablename = "shops"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class AlbumShops(ormar.Model):
    class Meta:
        tablename = "albums_x_shops"
        metadata = metadata
        database = database


class Album(ormar.Model):
    class Meta:
        tablename = "albums"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    shops: List[Shop] = ormar.ManyToMany(to=Shop, through=AlbumShops)


class Track(ormar.Model):
    class Meta:
        tablename = "tracks"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    album: Optional[Album] = ormar.ForeignKey(Album)
    title: str = ormar.String(max_length=100)
    position: int = ormar.Integer()
    tonation: Optional[Tonation] = ormar.ForeignKey(Tonation)


class Cover(ormar.Model):
    class Meta:
        tablename = "covers"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    album: Optional[Album] = ormar.ForeignKey(Album, related_name="cover_pictures")
    title: str = ormar.String(max_length=100)
    artist: str = ormar.String(max_length=200, nullable=True)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_prefetch_related():
    async with database:
        async with database.transaction(force_rollback=True):
            album = Album(name="Malibu")
            await album.save()
            ton1 = await Tonation.objects.create(name='B-mol')
            await Track.objects.create(album=album, title="The Bird", position=1, tonation=ton1)
            await Track.objects.create(album=album, title="Heart don't stand a chance", position=2, tonation=ton1)
            await Track.objects.create(album=album, title="The Waters", position=3, tonation=ton1)
            await Cover.objects.create(title='Cover1', album=album, artist='Artist 1')
            await Cover.objects.create(title='Cover2', album=album, artist='Artist 2')

            fantasies = Album(name="Fantasies")
            await fantasies.save()
            await Track.objects.create(album=fantasies, title="Help I'm Alive", position=1)
            await Track.objects.create(album=fantasies, title="Sick Muse", position=2)
            await Track.objects.create(album=fantasies, title="Satellite Mind", position=3)
            await Cover.objects.create(title='Cover3', album=fantasies, artist='Artist 3')
            await Cover.objects.create(title='Cover4', album=fantasies, artist='Artist 4')

            album = await Album.objects.filter(name='Malibu').prefetch_related(
                ['tracks__tonation', 'cover_pictures']).get()
            assert len(album.tracks) == 3
            assert album.tracks[0].title == 'The Bird'
            assert len(album.cover_pictures) == 2
            assert album.cover_pictures[0].title == 'Cover1'
            assert album.tracks[0].tonation.name == album.tracks[2].tonation.name == 'B-mol'

            albums = await Album.objects.prefetch_related('tracks').all()
            assert len(albums[0].tracks) == 3
            assert len(albums[1].tracks) == 3
            assert albums[0].tracks[0].title == "The Bird"
            assert albums[1].tracks[0].title == "Help I'm Alive"

            track = await Track.objects.prefetch_related(["album__cover_pictures"]).get(title="The Bird")
            assert track.album.name == "Malibu"
            assert len(track.album.cover_pictures) == 2
            assert track.album.cover_pictures[0].artist == 'Artist 1'

            track = await Track.objects.prefetch_related(["album__cover_pictures"]).exclude_fields(
                'album__cover_pictures__artist').get(title="The Bird")
            assert track.album.name == "Malibu"
            assert len(track.album.cover_pictures) == 2
            assert track.album.cover_pictures[0].artist is None

            tracks = await Track.objects.prefetch_related("album").all()
            assert len(tracks) == 6


@pytest.mark.asyncio
async def test_prefetch_related_with_many_to_many():
    async with database:
        async with database.transaction(force_rollback=True):
            shop1 = await Shop.objects.create(name='Shop 1')
            shop2 = await Shop.objects.create(name='Shop 2')
            album = Album(name="Malibu")
            await album.save()
            await album.shops.add(shop1)
            await album.shops.add(shop2)

            await Track.objects.create(album=album, title="The Bird", position=1)
            await Track.objects.create(album=album, title="Heart don't stand a chance", position=2)
            await Track.objects.create(album=album, title="The Waters", position=3)
            await Cover.objects.create(title='Cover1', album=album, artist='Artist 1')
            await Cover.objects.create(title='Cover2', album=album, artist='Artist 2')

            track = await Track.objects.prefetch_related(["album__cover_pictures", "album__shops"]).get(
                title="The Bird")
            assert track.album.name == "Malibu"
            assert len(track.album.cover_pictures) == 2
            assert track.album.cover_pictures[0].artist == 'Artist 1'

            assert len(track.album.shops) == 2


@pytest.mark.asyncio
async def test_prefetch_related_empty():
    async with database:
        async with database.transaction(force_rollback=True):
            await Track.objects.create(title="The Bird", position=1)
            track = await Track.objects.prefetch_related(["album__cover_pictures"]).get(title="The Bird")
            assert track.title == 'The Bird'
            assert track.album is None
