from typing import Optional

import databases
import pytest
import pytest_asyncio
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class Band(ormar.Model):
    class Meta:
        tablename = "bands"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class ArtistsBands(ormar.Model):
    class Meta:
        tablename = "artists_x_bands"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)


class Artist(ormar.Model):
    class Meta:
        tablename = "artists"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    bands = ormar.ManyToMany(Band, through=ArtistsBands)


class Album(ormar.Model):
    class Meta:
        tablename = "albums"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    artist: Optional[Artist] = ormar.ForeignKey(Artist, ondelete="CASCADE")


class Track(ormar.Model):
    class Meta:
        tablename = "tracks"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    album: Optional[Album] = ormar.ForeignKey(Album, ondelete="CASCADE")
    title: str = ormar.String(max_length=100)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest_asyncio.fixture(scope="function")
async def cleanup():
    yield
    async with database:
        await Band.objects.delete(each=True)
        await Artist.objects.delete(each=True)


@pytest.mark.asyncio
async def test_simple_cascade(cleanup):
    async with database:
        artist = await Artist(name="Dr Alban").save()
        await Album(name="Jamaica", artist=artist).save()
        await Artist.objects.delete(id=artist.id)
        artists = await Artist.objects.all()
        assert len(artists) == 0

        albums = await Album.objects.all()
        assert len(albums) == 0


@pytest.mark.asyncio
async def test_nested_cascade(cleanup):
    async with database:
        artist = await Artist(name="Dr Alban").save()
        album = await Album(name="Jamaica", artist=artist).save()
        await Track(title="Yuhu", album=album).save()

        await Artist.objects.delete(id=artist.id)

        artists = await Artist.objects.all()
        assert len(artists) == 0

        albums = await Album.objects.all()
        assert len(albums) == 0

        tracks = await Track.objects.all()
        assert len(tracks) == 0


@pytest.mark.asyncio
async def test_many_to_many_cascade(cleanup):
    async with database:
        artist = await Artist(name="Dr Alban").save()
        band = await Band(name="Scorpions").save()
        await artist.bands.add(band)

        check = await Artist.objects.select_related("bands").get()
        assert check.bands[0].name == "Scorpions"

        await Artist.objects.delete(id=artist.id)

        artists = await Artist.objects.all()
        assert len(artists) == 0

        bands = await Band.objects.all()
        assert len(bands) == 1

        connections = await ArtistsBands.objects.all()
        assert len(connections) == 0


@pytest.mark.asyncio
async def test_reverse_many_to_many_cascade(cleanup):
    async with database:
        artist = await Artist(name="Dr Alban").save()
        band = await Band(name="Scorpions").save()
        await artist.bands.add(band)

        check = await Artist.objects.select_related("bands").get()
        assert check.bands[0].name == "Scorpions"

        await Band.objects.delete(id=band.id)

        artists = await Artist.objects.all()
        assert len(artists) == 1

        connections = await ArtistsBands.objects.all()
        assert len(connections) == 0

        bands = await Band.objects.all()
        assert len(bands) == 0
