from typing import Any, Optional, TYPE_CHECKING

import databases
import pytest
import sqlalchemy

import ormar
from ormar.relations.querysetproxy import QuerysetProxy
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class Publisher(ormar.Model):
    class Meta(BaseMeta):
        tablename = "publishers"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Author(ormar.Model):
    class Meta(BaseMeta):
        tablename = "authors"
        order_by = ["-name"]

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    publishers = ormar.ManyToMany(Publisher)


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
    _ = str(book)


@pytest.mark.asyncio
async def test_types() -> None:
    async with database:
        query = Book.objects
        publisher = await Publisher(name="Test publisher").save()
        author = await Author.objects.create(name="Test Author")
        await author.publishers.add(publisher)
        author2 = await Author.objects.select_related("publishers").get()
        publishers = author2.publishers
        publisher2 = await Publisher.objects.select_related("authors").get()
        authors = publisher2.authors
        assert authors[0] == author
        for author in authors:
            pass
            # if TYPE_CHECKING:  # pragma: no cover
            #     reveal_type(author)  # iter of relation proxy
        book = await Book.objects.create(title="Test", author=author)
        book2 = await Book.objects.select_related("author").get()
        books = await Book.objects.select_related("author").all()
        author_books = await author.books.all()
        assert book.author.name == "Test Author"
        assert book2.author.name == "Test Author"
        # if TYPE_CHECKING:  # pragma: no cover
        #     reveal_type(publisher)  # model method
        #     reveal_type(publishers)  # many to many
        #     reveal_type(publishers[0])  # item in m2m list
        #     reveal_type(next(p for p in publishers))  # item in m2m iterator
        #     # getting relation without __getattribute__
        #     reveal_type(authors)  # reverse many to many  # TODO: wrong
        #     reveal_type(book2)  # queryset get
        #     reveal_type(books)  # queryset all
        #     reveal_type(book)  # queryset - create
        #     reveal_type(query)  # queryset itself
        #     reveal_type(book.author)  # fk
        #     reveal_type(author.books)  # reverse fk relation proxy  # TODO: wrong
        #     reveal_type(author)  # another test for queryset get different model
        #     reveal_type(book.author.name)  # field on related model
        #     reveal_type(author_books)  # querysetproxy result for fk  # TODO: wrong
        #     reveal_type(author_books[0])  # item in qs proxy for fk  # TODO: wrong
        assert_type(book)
