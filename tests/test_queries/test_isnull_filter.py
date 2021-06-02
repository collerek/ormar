from typing import Optional

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


class Author(ormar.Model):
    class Meta(BaseMeta):
        tablename = "authors"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Book(ormar.Model):
    class Meta(BaseMeta):
        tablename = "books"

    id: int = ormar.Integer(primary_key=True)
    author: Optional[Author] = ormar.ForeignKey(Author)
    title: str = ormar.String(max_length=100)
    year: int = ormar.Integer(nullable=True)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_is_null():
    async with database:
        tolkien = await Author.objects.create(name="J.R.R. Tolkien")
        await Book.objects.create(author=tolkien, title="The Hobbit")
        await Book.objects.create(
            author=tolkien, title="The Lord of the Rings", year=1955
        )
        await Book.objects.create(author=tolkien, title="The Silmarillion", year=1977)

        books = await Book.objects.all(year__isnull=True)
        assert len(books) == 1
        assert books[0].year is None
        assert books[0].title == "The Hobbit"

        books = await Book.objects.all(year__isnull=False)
        assert len(books) == 2

        tolkien = await Author.objects.select_related("books").get(
            books__year__isnull=True
        )
        assert len(tolkien.books) == 1
        assert tolkien.books[0].year is None
        assert tolkien.books[0].title == "The Hobbit"

        tolkien = (
            await Author.objects.select_related("books")
            .paginate(1, 10)
            .get(books__year__isnull=True)
        )
        assert len(tolkien.books) == 1
        assert tolkien.books[0].year is None
        assert tolkien.books[0].title == "The Hobbit"

        tolkien = await Author.objects.select_related("books").get(
            books__year__isnull=False
        )
        assert len(tolkien.books) == 2
        assert tolkien.books[0].year == 1955
        assert tolkien.books[0].title == "The Lord of the Rings"
