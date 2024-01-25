from typing import List, Optional

import databases
import ormar
import pytest
import sqlalchemy

from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Child(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename="children",
        metadata=metadata,
        database=database,
    )

    id: int = ormar.Integer(name="child_id", primary_key=True)
    first_name: str = ormar.String(name="fname", max_length=100)
    last_name: str = ormar.String(name="lname", max_length=100)
    born_year: int = ormar.Integer(name="year_born", nullable=True)


class Artist(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename="artists",
        metadata=metadata,
        database=database,
    )

    id: int = ormar.Integer(name="artist_id", primary_key=True)
    first_name: str = ormar.String(name="fname", max_length=100)
    last_name: str = ormar.String(name="lname", max_length=100)
    born_year: int = ormar.Integer(name="year")
    children: Optional[List[Child]] = ormar.ManyToMany(Child)


class Album(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename="music_albums",
        metadata=metadata,
        database=database,
    )

    id: int = ormar.Integer(name="album_id", primary_key=True)
    name: str = ormar.String(name="album_name", max_length=100)
    artist: Optional[Artist] = ormar.ForeignKey(Artist, name="artist_id")


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


def test_table_structure():
    assert "album_id" in [x.name for x in Album.ormar_config.table.columns]
    assert "album_name" in [x.name for x in Album.ormar_config.table.columns]
    assert "fname" in [x.name for x in Artist.ormar_config.table.columns]
    assert "lname" in [x.name for x in Artist.ormar_config.table.columns]
    assert "year" in [x.name for x in Artist.ormar_config.table.columns]


@pytest.mark.asyncio
async def test_working_with_aliases():
    async with database:
        async with database.transaction(force_rollback=True):
            artist = await Artist.objects.create(
                first_name="Ted", last_name="Mosbey", born_year=1975
            )
            await Album.objects.create(name="Aunt Robin", artist=artist)

            await artist.children.create(
                first_name="Son", last_name="1", born_year=1990
            )
            await artist.children.create(
                first_name="Son", last_name="2", born_year=1995
            )

            await artist.children.create(
                first_name="Son", last_name="3", born_year=1998
            )

            album = await Album.objects.select_related("artist").first()
            assert album.artist.last_name == "Mosbey"

            assert album.artist.id is not None
            assert album.artist.first_name == "Ted"
            assert album.artist.born_year == 1975

            assert album.name == "Aunt Robin"

            artist = await Artist.objects.select_related("children").get()
            assert len(artist.children) == 3
            assert artist.children[0].first_name == "Son"
            assert artist.children[1].last_name == "2"
            assert artist.children[2].last_name == "3"

            await artist.update(last_name="Bundy")
            await Artist.objects.filter(pk=artist.pk).update(born_year=1974)

            artist = await Artist.objects.select_related("children").get()
            assert artist.last_name == "Bundy"
            assert artist.born_year == 1974

            artist = (
                await Artist.objects.select_related("children")
                .fields(
                    [
                        "first_name",
                        "last_name",
                        "born_year",
                        "children__first_name",
                        "children__last_name",
                    ]
                )
                .get()
            )
            assert artist.children[0].born_year is None


@pytest.mark.asyncio
async def test_bulk_operations_and_fields():
    async with database:
        d1 = Child(first_name="Daughter", last_name="1", born_year=1990)
        d2 = Child(first_name="Daughter", last_name="2", born_year=1991)
        await Child.objects.bulk_create([d1, d2])

        children = await Child.objects.filter(first_name="Daughter").all()
        assert len(children) == 2
        assert children[0].last_name == "1"

        for child in children:
            child.born_year = child.born_year - 100

        await Child.objects.bulk_update(children)

        children = await Child.objects.filter(first_name="Daughter").all()
        assert len(children) == 2
        assert children[0].born_year == 1890

        children = await Child.objects.fields(["first_name", "last_name"]).all()
        assert len(children) == 2
        for child in children:
            assert child.born_year is None

        await children[0].load()
        await children[0].delete()
        children = await Child.objects.all()
        assert len(children) == 1


@pytest.mark.asyncio
async def test_working_with_aliases_get_or_create():
    async with database:
        async with database.transaction(force_rollback=True):
            artist, created = await Artist.objects.get_or_create(
                first_name="Teddy", last_name="Bear", born_year=2020
            )
            assert artist.pk is not None
            assert created is True

            artist2, created = await Artist.objects.get_or_create(
                first_name="Teddy", last_name="Bear", born_year=2020
            )
            assert artist == artist2
            assert created is False

            art3 = artist2.dict()
            art3["born_year"] = 2019
            await Artist.objects.update_or_create(**art3)

            artist3 = await Artist.objects.get(last_name="Bear")
            assert artist3.born_year == 2019

            artists = await Artist.objects.all()
            assert len(artists) == 1
