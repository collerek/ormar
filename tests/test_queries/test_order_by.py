from typing import List, Optional

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
    sort_order: Optional[int] = ormar.Integer(nullable=True)


class Owner(ormar.Model):
    class Meta:
        tablename = "owners"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class AliasNested(ormar.Model):
    class Meta:
        tablename = "aliases_nested"
        metadata = metadata
        database = database

    id: int = ormar.Integer(name="alias_id", primary_key=True)
    name: str = ormar.String(name="alias_name", max_length=100)


class AliasTest(ormar.Model):
    class Meta:
        tablename = "aliases"
        metadata = metadata
        database = database

    id: int = ormar.Integer(name="alias_id", primary_key=True)
    name: str = ormar.String(name="alias_name", max_length=100)
    nested = ormar.ForeignKey(AliasNested, name="nested_alias")


class Toy(ormar.Model):
    class Meta:
        tablename = "toys"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    owner: Owner = ormar.ForeignKey(Owner)


class Factory(ormar.Model):
    class Meta:
        tablename = "factories"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Car(ormar.Model):
    class Meta:
        tablename = "cars"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    factory: Optional[Factory] = ormar.ForeignKey(Factory)


class User(ormar.Model):
    class Meta:
        tablename = "users"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    cars: List[Car] = ormar.ManyToMany(Car)


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

        songs = await Song.objects.order_by(Song.sort_order.desc()).all()
        assert songs[0].name == "Song 3"
        assert songs[1].name == "Song 2"
        assert songs[2].name == "Song 1"

        songs = await Song.objects.order_by("sort_order").all()
        assert songs[0].name == "Song 1"
        assert songs[1].name == "Song 2"
        assert songs[2].name == "Song 3"

        songs = await Song.objects.order_by(Song.sort_order.asc()).all()
        assert songs[0].name == "Song 1"
        assert songs[1].name == "Song 2"
        assert songs[2].name == "Song 3"

        songs = await Song.objects.order_by("name").all()
        assert songs[0].name == "Song 1"
        assert songs[1].name == "Song 2"
        assert songs[2].name == "Song 3"

        songs = await Song.objects.order_by("name").limit(2).all()
        assert len(songs) == 2
        assert songs[0].name == "Song 1"
        assert songs[1].name == "Song 2"

        await Song.objects.create(name="Song 4", sort_order=1)

        songs = await Song.objects.order_by(["sort_order", "name"]).all()
        assert songs[0].name == "Song 1"
        assert songs[1].name == "Song 4"
        assert songs[2].name == "Song 2"
        assert songs[3].name == "Song 3"

        songs = await Song.objects.order_by(
            [Song.sort_order.asc(), Song.name.asc()]
        ).all()
        assert songs[0].name == "Song 1"
        assert songs[1].name == "Song 4"
        assert songs[2].name == "Song 2"
        assert songs[3].name == "Song 3"

        await Song.objects.create(name="Song 5")

        songs = await Song.objects.order_by(Song.sort_order.asc(nulls_last=True)).all()
        assert songs[0].name in "Song 1", "Song 4"
        assert songs[1].name in "Song 1", "Song 4"
        assert songs[2].name == "Song 2"
        assert songs[3].name == "Song 3"
        assert songs[4].name == "Song 5"

        songs = await Song.objects.order_by(Song.sort_order.asc(nulls_first=True)).all()
        assert songs[0].name == "Song 5"
        assert songs[1].name in "Song 1", "Song 4"
        assert songs[2].name in "Song 1", "Song 4"
        assert songs[3].name == "Song 2"
        assert songs[4].name == "Song 3"

        songs = await Song.objects.order_by(Song.sort_order.desc(nulls_last=True)).all()
        assert songs[0].name == "Song 3"
        assert songs[1].name == "Song 2"
        assert songs[2].name in "Song 1", "Song 4"
        assert songs[3].name in "Song 1", "Song 4"
        assert songs[4].name == "Song 5"

        songs = await Song.objects.order_by(
            Song.sort_order.desc(nulls_first=True)
        ).all()
        assert songs[0].name == "Song 5"
        assert songs[1].name == "Song 3"
        assert songs[2].name == "Song 2"
        assert songs[3].name in "Song 1", "Song 4"
        assert songs[4].name in "Song 1", "Song 4"

        with pytest.raises(ValueError):
            await Song.objects.order_by(
                Song.sort_order.asc(nulls_last=True, nulls_first=True)
            ).all()


@pytest.mark.asyncio
async def test_sort_order_on_related_model():
    async with database:
        aphrodite = await Owner.objects.create(name="Aphrodite")
        hermes = await Owner.objects.create(name="Hermes")
        zeus = await Owner.objects.create(name="Zeus")

        await Toy.objects.create(name="Toy 4", owner=zeus)
        await Toy.objects.create(name="Toy 5", owner=hermes)
        await Toy.objects.create(name="Toy 2", owner=aphrodite)
        await Toy.objects.create(name="Toy 1", owner=zeus)
        await Toy.objects.create(name="Toy 3", owner=aphrodite)
        await Toy.objects.create(name="Toy 6", owner=hermes)

        toys = await Toy.objects.select_related("owner").order_by("name").all()
        assert [x.name.replace("Toy ", "") for x in toys] == [
            str(x + 1) for x in range(6)
        ]
        assert toys[0].owner == zeus
        assert toys[1].owner == aphrodite

        toys = await Toy.objects.select_related("owner").order_by("owner__name").all()
        assert toys[0].owner.name == toys[1].owner.name == "Aphrodite"
        assert toys[2].owner.name == toys[3].owner.name == "Hermes"
        assert toys[4].owner.name == toys[5].owner.name == "Zeus"

        owner = (
            await Owner.objects.select_related("toys")
            .order_by("toys__name")
            .filter(name="Zeus")
            .get()
        )
        assert owner.toys[0].name == "Toy 1"
        assert owner.toys[1].name == "Toy 4"

        owner = (
            await Owner.objects.select_related("toys")
            .order_by("-toys__name")
            .filter(name="Zeus")
            .get()
        )
        assert owner.toys[0].name == "Toy 4"
        assert owner.toys[1].name == "Toy 1"

        owners = (
            await Owner.objects.select_related("toys")
            .order_by("-toys__name")
            .filter(name__in=["Zeus", "Hermes"])
            .all()
        )
        assert owners[0].toys[0].name == "Toy 6"
        assert owners[0].toys[1].name == "Toy 5"
        assert owners[0].name == "Hermes"

        assert owners[1].toys[0].name == "Toy 4"
        assert owners[1].toys[1].name == "Toy 1"
        assert owners[1].name == "Zeus"

        await Toy.objects.create(name="Toy 7", owner=zeus)

        owners = (
            await Owner.objects.select_related("toys")
            .order_by("-toys__name")
            .filter(name__in=["Zeus", "Hermes"])
            .all()
        )
        assert owners[0].toys[0].name == "Toy 7"
        assert owners[0].toys[1].name == "Toy 4"
        assert owners[0].toys[2].name == "Toy 1"
        assert owners[0].name == "Zeus"

        assert owners[1].toys[0].name == "Toy 6"
        assert owners[1].toys[1].name == "Toy 5"
        assert owners[1].name == "Hermes"

        toys = (
            await Toy.objects.select_related("owner")
            .order_by(["owner__name", "name"])
            .limit(2)
            .all()
        )
        assert len(toys) == 2
        assert toys[0].name == "Toy 2"
        assert toys[1].name == "Toy 3"


@pytest.mark.asyncio
async def test_sort_order_on_many_to_many():
    async with database:
        factory1 = await Factory.objects.create(name="Factory 1")
        factory2 = await Factory.objects.create(name="Factory 2")

        car1 = await Car.objects.create(name="Buggy", factory=factory1)
        car2 = await Car.objects.create(name="Volkswagen", factory=factory2)
        car3 = await Car.objects.create(name="Ferrari", factory=factory1)
        car4 = await Car.objects.create(name="Volvo", factory=factory2)
        car5 = await Car.objects.create(name="Skoda", factory=factory1)
        car6 = await Car.objects.create(name="Seat", factory=factory2)

        user1 = await User.objects.create(name="Mark")
        user2 = await User.objects.create(name="Julie")

        await user1.cars.add(car1)
        await user1.cars.add(car3)
        await user1.cars.add(car4)
        await user1.cars.add(car5)

        await user2.cars.add(car1)
        await user2.cars.add(car2)
        await user2.cars.add(car5)
        await user2.cars.add(car6)

        user = (
            await User.objects.select_related("cars")
            .filter(name="Mark")
            .order_by("cars__name")
            .get()
        )
        assert user.cars[0].name == "Buggy"
        assert user.cars[1].name == "Ferrari"
        assert user.cars[2].name == "Skoda"
        assert user.cars[3].name == "Volvo"

        user = (
            await User.objects.select_related("cars")
            .filter(name="Mark")
            .order_by("-cars__name")
            .get()
        )
        assert user.cars[3].name == "Buggy"
        assert user.cars[2].name == "Ferrari"
        assert user.cars[1].name == "Skoda"
        assert user.cars[0].name == "Volvo"

        users = await User.objects.select_related("cars").order_by("-cars__name").all()
        assert users[0].name == "Mark"
        assert users[1].cars[0].name == "Volkswagen"
        assert users[1].cars[1].name == "Skoda"
        assert users[1].cars[2].name == "Seat"
        assert users[1].cars[3].name == "Buggy"

        users = (
            await User.objects.select_related(["cars__factory"])
            .order_by(["-cars__factory__name", "cars__name"])
            .all()
        )

        assert users[0].name == "Julie"
        assert users[0].cars[0].name == "Seat"
        assert users[0].cars[1].name == "Volkswagen"
        assert users[0].cars[2].name == "Buggy"
        assert users[0].cars[3].name == "Skoda"

        assert users[1].name == "Mark"
        assert users[1].cars[0].name == "Volvo"
        assert users[1].cars[1].name == "Buggy"
        assert users[1].cars[2].name == "Ferrari"
        assert users[1].cars[3].name == "Skoda"


@pytest.mark.asyncio
async def test_sort_order_with_aliases():
    async with database:
        al1 = await AliasTest.objects.create(name="Test4")
        al2 = await AliasTest.objects.create(name="Test2")
        al3 = await AliasTest.objects.create(name="Test1")
        al4 = await AliasTest.objects.create(name="Test3")

        aliases = await AliasTest.objects.order_by("-name").all()
        assert [alias.name[-1] for alias in aliases] == ["4", "3", "2", "1"]

        nest1 = await AliasNested.objects.create(name="Try1")
        nest2 = await AliasNested.objects.create(name="Try2")
        nest3 = await AliasNested.objects.create(name="Try3")
        nest4 = await AliasNested.objects.create(name="Try4")

        al1.nested = nest1
        await al1.update()

        al2.nested = nest2
        await al2.update()

        al3.nested = nest3
        await al3.update()

        al4.nested = nest4
        await al4.update()

        aliases = (
            await AliasTest.objects.select_related("nested")
            .order_by("-nested__name")
            .all()
        )
        assert aliases[0].nested.name == "Try4"
        assert aliases[1].nested.name == "Try3"
        assert aliases[2].nested.name == "Try2"
        assert aliases[3].nested.name == "Try1"
