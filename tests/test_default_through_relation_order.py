from typing import List
from uuid import UUID, uuid4

import databases
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class Animal(ormar.Model):
    class Meta(BaseMeta):
        tablename = "animals"

    id: UUID = ormar.UUID(primary_key=True, default=uuid4)
    name: str = ormar.Text(default="")
    # favoriteHumans


class Link(ormar.Model):
    class Meta(BaseMeta):
        tablename = "link_table"

    id: int = ormar.Integer(primary_key=True)
    animal_order: int = ormar.Integer(nullable=True)
    human_order: int = ormar.Integer(nullable=True)


class Human(ormar.Model):
    class Meta(BaseMeta):
        tablename = "humans"

    id: UUID = ormar.UUID(primary_key=True, default=uuid4)
    name: str = ormar.Text(default="")
    favoriteAnimals: List[Animal] = ormar.ManyToMany(
        Animal,
        through=Link,
        related_name="favoriteHumans",
        orders_by=["link__animal_order"],
        related_orders_by=["link__human_order"],
    )


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_ordering_by_through_on_m2m_field():
    async with database:
        alice = await Human(name="Alice").save()
        bob = await Human(name="Bob").save()
        charlie = await Human(name="Charlie").save()

        spot = await Animal(name="Spot").save()
        kitty = await Animal(name="Kitty").save()
        noodle = await Animal(name="Noodle").save()

        # you need to add them in order anyway so can provide order explicitly
        # if you have a lot of them a list with enumerate might be an option
        await alice.favoriteAnimals.add(noodle, animal_order=0, human_order=0)
        await alice.favoriteAnimals.add(spot, animal_order=1, human_order=0)
        await alice.favoriteAnimals.add(kitty, animal_order=2, human_order=0)

        # you dont have to reload queries on queryset clears the existing related
        # alice = await alice.reload()
        await alice.load_all()
        assert [x.name for x in alice.favoriteAnimals] == ["Noodle", "Spot", "Kitty"]

        await bob.favoriteAnimals.add(noodle, animal_order=0, human_order=1)
        await bob.favoriteAnimals.add(kitty, animal_order=1, human_order=1)
        await bob.favoriteAnimals.add(spot, animal_order=2, human_order=1)

        await bob.load_all()
        assert [x.name for x in bob.favoriteAnimals] == ["Noodle", "Kitty", "Spot"]

        await charlie.favoriteAnimals.add(kitty, animal_order=0, human_order=2)
        await charlie.favoriteAnimals.add(noodle, animal_order=1, human_order=2)
        await charlie.favoriteAnimals.add(spot, animal_order=2, human_order=2)

        await charlie.load_all()
        assert [x.name for x in charlie.favoriteAnimals] == ["Kitty", "Noodle", "Spot"]

        animals = [noodle, kitty, spot]
        for animal in animals:
            await animal.load_all()
            assert [x.name for x in animal.favoriteHumans] == [
                "Alice",
                "Bob",
                "Charlie",
            ]

        zack = await Human(name="Zack").save()

        async def reorder_humans(animal, new_ordered_humans):
            noodle_links = await Link.objects.filter(animal=animal).all()
            for link in noodle_links:
                link.human_order = next(
                    (
                        i
                        for i, x in enumerate(new_ordered_humans)
                        if x.pk == link.human.pk
                    ),
                    None,
                )
            await Link.objects.bulk_update(noodle_links, columns=["human_order"])

        await noodle.favoriteHumans.add(zack, animal_order=0, human_order=0)
        await reorder_humans(noodle, [zack, alice, bob, charlie])
        await noodle.load_all()
        assert [x.name for x in noodle.favoriteHumans] == [
            "Zack",
            "Alice",
            "Bob",
            "Charlie",
        ]

        await zack.load_all()
        assert [x.name for x in zack.favoriteAnimals] == ["Noodle"]

        humans = noodle.favoriteHumans
        humans.insert(1, humans.pop(0))
        await reorder_humans(noodle, humans)
        await noodle.load_all()
        assert [x.name for x in noodle.favoriteHumans] == [
            "Alice",
            "Zack",
            "Bob",
            "Charlie",
        ]

        humans.insert(2, humans.pop(1))
        await reorder_humans(noodle, humans)
        await noodle.load_all()
        assert [x.name for x in noodle.favoriteHumans] == [
            "Alice",
            "Bob",
            "Zack",
            "Charlie",
        ]

        humans.insert(3, humans.pop(2))
        await reorder_humans(noodle, humans)
        await noodle.load_all()
        assert [x.name for x in noodle.favoriteHumans] == [
            "Alice",
            "Bob",
            "Charlie",
            "Zack",
        ]

        await kitty.favoriteHumans.remove(bob)
        await kitty.load_all()
        assert [x.name for x in kitty.favoriteHumans] == ["Alice", "Charlie"]

        bob = await noodle.favoriteHumans.get(pk=bob.pk)
        assert bob.link.human_order == 1
        await noodle.favoriteHumans.remove(
            await noodle.favoriteHumans.filter(link__human_order=2).get()
        )
        await noodle.load_all()
        assert [x.name for x in noodle.favoriteHumans] == ["Alice", "Bob", "Zack"]
