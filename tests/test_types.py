from typing import Any, Optional, TYPE_CHECKING

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
        order_by = ["-name"]

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Book(ormar.Model):
    class Meta(BaseMeta):
        tablename = "books"
        order_by = ["year", "-ranking"]

    id: int = ormar.Integer(primary_key=True)
    author = ormar.ForeignKey(Author)
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


def assert_type(book: Book):
    print(book)


@pytest.mark.asyncio
async def test_types() -> None:
    async with database:
        query = Book.objects
        author = await Author.objects.create(name='Test Author')
        book = await Book.objects.create(title='Test', author=author)
        book2 = await Book.objects.select_related('author').get()
        books = await Book.objects.select_related('author').all()
        author_books = await author.books.all()
        assert book.author.name == 'Test Author'
        assert book2.author.name == 'Test Author'
        if TYPE_CHECKING:  # pragma: no cover
            reveal_type(book._orm._relations['author'].to)
            reveal_type(book2)
            reveal_type(query)
            reveal_type(book)
            reveal_type(book.author)
            reveal_type(author)
            reveal_type(book.author.name)
            reveal_type(author.books)
            reveal_type(author.books._queryset)
            reveal_type(author_books)
            reveal_type(books)
        assert_type(book)
