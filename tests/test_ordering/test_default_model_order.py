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
        orders_by = ["-name"]

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Book(ormar.Model):
    class Meta(BaseMeta):
        tablename = "books"
        orders_by = ["year", "-ranking"]

    id: int = ormar.Integer(primary_key=True)
    author: Optional[Author] = ormar.ForeignKey(Author)
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
async def test_default_orders_is_applied():
    async with database:
        tolkien = await Author(name="J.R.R. Tolkien").save()
        sapkowski = await Author(name="Andrzej Sapkowski").save()
        king = await Author(name="Stephen King").save()
        lewis = await Author(name="C.S Lewis").save()

        authors = await Author.objects.all()
        assert authors[0] == king
        assert authors[1] == tolkien
        assert authors[2] == lewis
        assert authors[3] == sapkowski

        authors = await Author.objects.order_by("name").all()
        assert authors[3] == king
        assert authors[2] == tolkien
        assert authors[1] == lewis
        assert authors[0] == sapkowski


@pytest.mark.asyncio
async def test_default_orders_is_applied_on_related():
    async with database:
        tolkien = await Author(name="J.R.R. Tolkien").save()
        silmarillion = await Book(
            author=tolkien, title="The Silmarillion", year=1977
        ).save()
        lotr = await Book(
            author=tolkien, title="The Lord of the Rings", year=1955
        ).save()
        hobbit = await Book(author=tolkien, title="The Hobbit", year=1933).save()

        await tolkien.books.all()
        assert tolkien.books[0] == hobbit
        assert tolkien.books[1] == lotr
        assert tolkien.books[2] == silmarillion

        await tolkien.books.order_by("-title").all()
        assert tolkien.books[2] == hobbit
        assert tolkien.books[1] == lotr
        assert tolkien.books[0] == silmarillion


@pytest.mark.asyncio
async def test_default_orders_is_applied_on_related_two_fields():
    async with database:
        sanders = await Author(name="Brandon Sanderson").save()
        twok = await Book(
            author=sanders, title="The Way of Kings", year=2010, ranking=10
        ).save()
        bret = await Author(name="Peter V. Bret").save()
        tds = await Book(
            author=bret, title="The Desert Spear", year=2010, ranking=9
        ).save()

        books = await Book.objects.all()
        assert books[0] == twok
        assert books[1] == tds
