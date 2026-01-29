from typing import Optional

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
    ormar_config = base_ormar_config.copy(tablename="books", order_by=["-ranking"])

    id: int = ormar.Integer(primary_key=True)
    author: Optional[Author] = ormar.ForeignKey(
        Author, orders_by=["name"], related_orders_by=["-year"]
    )
    title: str = ormar.String(max_length=100)
    year: Optional[int] = ormar.Integer(nullable=True)
    ranking: Optional[int] = ormar.Integer(nullable=True)


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

        tolkien = (
            await Author.objects.select_related("books").order_by("books__title").get()
        )
        assert tolkien.books[0] == hobbit
        assert tolkien.books[1] == lotr
        assert tolkien.books[2] == silmarillion
