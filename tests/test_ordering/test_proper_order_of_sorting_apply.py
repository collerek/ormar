from typing import Optional

import databases
import pytest
import pytest_asyncio
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class Author(ormar.Model):
    class Meta(BaseMeta):
        tablename = "authors"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Book(ormar.Model):
    class Meta(BaseMeta):
        tablename = "books"
        orders_by = ["-ranking"]

    id: int = ormar.Integer(primary_key=True)
    author: Optional[Author] = ormar.ForeignKey(
        Author, orders_by=["name"], related_orders_by=["-year"]
    )
    title: str = ormar.String(max_length=100)
    year: int = ormar.Integer(nullable=True)
    ranking: int = ormar.Integer(nullable=True)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest_asyncio.fixture(autouse=True, scope="function")
async def cleanup():
    yield
    async with database:
        await Book.objects.delete(each=True)
        await Author.objects.delete(each=True)


@pytest.mark.asyncio
async def test_default_orders_is_applied_from_reverse_relation():
    async with database:
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
