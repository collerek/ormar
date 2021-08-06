from typing import List, Optional

import databases
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class RandomSet(ormar.Model):
    class Meta:
        tablename = "randoms"
        metadata = metadata
        database = database

    id: int = ormar.Integer(name="random_id", primary_key=True)
    name: str = ormar.String(max_length=100)


class Tonation(ormar.Model):
    class Meta:
        tablename = "tonations"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(name="tonation_name", max_length=100)
    rand_set: Optional[RandomSet] = ormar.ForeignKey(RandomSet)


class Division(ormar.Model):
    class Meta:
        tablename = "divisions"
        metadata = metadata
        database = database

    id: int = ormar.Integer(name="division_id", primary_key=True)
    name: str = ormar.String(max_length=100, nullable=True)


class Shop(ormar.Model):
    class Meta:
        tablename = "shops"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=True)
    division: Optional[Division] = ormar.ForeignKey(Division)


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
    name: str = ormar.String(max_length=100, nullable=True)
    shops: List[Shop] = ormar.ManyToMany(to=Shop, through=AlbumShops)


class Track(ormar.Model):
    class Meta:
        tablename = "tracks"
        metadata = metadata
        database = database

    id: int = ormar.Integer(name="track_id", primary_key=True)
    album: Optional[Album] = ormar.ForeignKey(Album)
    title: str = ormar.String(max_length=100)
    position: int = ormar.Integer()
    tonation: Optional[Tonation] = ormar.ForeignKey(Tonation, name="tonation_id")


class Cover(ormar.Model):
    class Meta:
        tablename = "covers"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    album: Optional[Album] = ormar.ForeignKey(
        Album, related_name="cover_pictures", name="album_id"
    )
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
async def test_prefetch_related_with_select_related():
    async with database:
        async with database.transaction(force_rollback=True):
            div = await Division.objects.create(name="Div 1")
            shop1 = await Shop.objects.create(name="Shop 1", division=div)
            shop2 = await Shop.objects.create(name="Shop 2", division=div)
            album = Album(name="Malibu")
            await album.save()
            await album.shops.add(shop1)
            await album.shops.add(shop2)

            await Cover.objects.create(title="Cover1", album=album, artist="Artist 1")
            await Cover.objects.create(title="Cover2", album=album, artist="Artist 2")

            test = await Cover.objects.all(album=1)
            assert test

            album = (
                await Album.objects.select_related(["tracks"])
                    .filter(name="Malibu")
                    .prefetch_related(["cover_pictures", "shops__division"])
                    .first()
            )

            assert len(album.tracks) == 0
            assert len(album.cover_pictures) == 2
            assert album.shops[0].division.name == "Div 1"
