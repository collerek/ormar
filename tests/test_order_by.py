import databases
import pytest
import sqlalchemy

import ormar
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
    sort_order: int = ormar.Integer()


class Owner(ormar.Model):
    class Meta:
        tablename = "owners"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Toy(ormar.Model):
    class Meta:
        tablename = "toys"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    owner: Owner = ormar.ForeignKey(Owner)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_sort_order_on_main_model():
    async with database:
        await Song.objects.create(name="Song 3", sort_order=3)
        await Song.objects.create(name="Song 1", sort_order=1)
        await Song.objects.create(name="Song 2", sort_order=2)

        songs = await Song.objects.all()
        assert songs[0].name == "Song 3"
        assert songs[1].name == "Song 1"
        assert songs[2].name == "Song 2"

        songs = await Song.objects.order_by("-sort_order").all()
        assert songs[0].name == "Song 3"
        assert songs[1].name == "Song 2"
        assert songs[2].name == "Song 1"

        songs = await Song.objects.order_by("sort_order").all()
        assert songs[0].name == "Song 1"
        assert songs[1].name == "Song 2"
        assert songs[2].name == "Song 3"

        songs = await Song.objects.order_by("name").all()
        assert songs[0].name == "Song 1"
        assert songs[1].name == "Song 2"
        assert songs[2].name == "Song 3"

        await Song.objects.create(name="Song 4", sort_order=1)

        songs = await Song.objects.order_by(["sort_order", "name"]).all()
        assert songs[0].name == "Song 1"
        assert songs[1].name == "Song 4"
        assert songs[2].name == "Song 2"
        assert songs[3].name == "Song 3"


@pytest.mark.asyncio
async def test_sort_order_on_related_model():
    async with database:
        aphrodite = await Owner.objects.create(name="Aphrodite")
        hermes = await Owner.objects.create(name="Hermes")
        zeus = await Owner.objects.create(name="Zeus")

        await Toy.objects.create(name="Toy 1", owner=zeus)
        await Toy.objects.create(name="Toy 5", owner=hermes)
        await Toy.objects.create(name="Toy 2", owner=aphrodite)
        await Toy.objects.create(name="Toy 4", owner=zeus)
        await Toy.objects.create(name="Toy 3", owner=aphrodite)
        await Toy.objects.create(name="Toy 6", owner=hermes)

        toys = await Toy.objects.select_related("owner").order_by("name").all()
        assert [x.name.replace("Toy ", "") for x in toys] == [
            str(x + 1) for x in range(6)
        ]
        assert toys[0].owner == zeus
        assert toys[1].owner == aphrodite

        toys = await Toy.objects.select_related("owner").order_by("owner__name").all()

        owner = (
            await Owner.objects.select_related("toys")
            .order_by("toys__name")
            .filter(name="Zeus")
            .all()
        )
