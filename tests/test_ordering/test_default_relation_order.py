from typing import Optional
from uuid import UUID, uuid4

import ormar
import pytest
import pytest_asyncio

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Author(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="authors")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Book(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="books")

    id: int = ormar.Integer(primary_key=True)
    author: Optional[Author] = ormar.ForeignKey(
        Author, orders_by=["name"], related_orders_by=["-year"]
    )
    title: str = ormar.String(max_length=100)
    year: Optional[int] = ormar.Integer(nullable=True)
    ranking: Optional[int] = ormar.Integer(nullable=True)


class Animal(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="animals")

    id: UUID = ormar.UUID(primary_key=True, default=uuid4)
    name: str = ormar.String(max_length=200)
    specie: str = ormar.String(max_length=200)


class Human(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="humans")

    id: UUID = ormar.UUID(primary_key=True, default=uuid4)
    name: str = ormar.Text(default="")
    pets: list[Animal] = ormar.ManyToMany(
        Animal,
        related_name="care_takers",
        orders_by=["specie", "-name"],
        related_orders_by=["name"],
    )


create_test_database = init_tests(base_ormar_config)


@pytest_asyncio.fixture(autouse=True, scope="function")
async def cleanup():
    yield
    async with base_ormar_config.database:
        await Book.objects.delete(each=True)
        await Author.objects.delete(each=True)


@pytest.mark.asyncio
async def test_default_orders_is_applied_from_reverse_relation():
    async with base_ormar_config.database:
        tolkien = await Author(name="J.R.R. Tolkien").save()
        hobbit = await Book(author=tolkien, title="The Hobbit", year=1933).save()
        silmarillion = await Book(
            author=tolkien, title="The Silmarillion", year=1977
        ).save()
        lotr = await Book(
            author=tolkien, title="The Lord of the Rings", year=1955
        ).save()

        tolkien = await Author.objects.select_related("books").get()
        assert tolkien.books[2] == hobbit
        assert tolkien.books[1] == lotr
        assert tolkien.books[0] == silmarillion


@pytest.mark.asyncio
async def test_default_orders_is_applied_from_relation():
    async with base_ormar_config.database:
        bret = await Author(name="Peter V. Bret").save()
        tds = await Book(
            author=bret, title="The Desert Spear", year=2010, ranking=9
        ).save()
        sanders = await Author(name="Brandon Sanderson").save()
        twok = await Book(
            author=sanders, title="The Way of Kings", year=2010, ranking=10
        ).save()

        books = await Book.objects.order_by("year").select_related("author").all()
        assert books[0] == twok
        assert books[1] == tds


@pytest.mark.asyncio
async def test_default_orders_is_applied_from_relation_on_m2m():
    async with base_ormar_config.database:
        alice = await Human(name="Alice").save()

        spot = await Animal(name="Spot", specie="Cat").save()
        zkitty = await Animal(name="ZKitty", specie="Cat").save()
        noodle = await Animal(name="Noodle", specie="Anaconda").save()

        await alice.pets.add(noodle)
        await alice.pets.add(spot)
        await alice.pets.add(zkitty)

        await alice.load_all()
        assert alice.pets[0] == noodle
        assert alice.pets[1] == zkitty
        assert alice.pets[2] == spot


@pytest.mark.asyncio
async def test_default_orders_is_applied_from_reverse_relation_on_m2m():
    async with base_ormar_config.database:
        max = await Animal(name="Max", specie="Dog").save()
        joe = await Human(name="Joe").save()
        zack = await Human(name="Zack").save()
        julia = await Human(name="Julia").save()

        await max.care_takers.add(joe)
        await max.care_takers.add(zack)
        await max.care_takers.add(julia)

        await max.load_all()
        assert max.care_takers[0] == joe
        assert max.care_takers[1] == julia
        assert max.care_takers[2] == zack
