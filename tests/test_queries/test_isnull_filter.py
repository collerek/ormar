from typing import Optional

import databases
import ormar
import pytest
import sqlalchemy

from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


base_ormar_config = ormar.OrmarConfig(
    metadata=metadata,
    database=database,
)


class Author(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="authors")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Book(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="books")

    id: int = ormar.Integer(primary_key=True)
    author: Optional[Author] = ormar.ForeignKey(Author)
    title: str = ormar.String(max_length=100)
    year: int = ormar.Integer(nullable=True)


class JsonModel(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        metadata=metadata,
        database=database,
        tablename="jsons",
    )

    id = ormar.Integer(primary_key=True)
    text_field = ormar.Text(nullable=True)
    json_field = ormar.JSON(nullable=True)
    json_not_null = ormar.JSON()


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


@pytest.mark.asyncio
async def test_isnull_json():
    async with database:
        author = await JsonModel.objects.create(json_not_null=None)
        assert author.json_field is None
        non_null_text_fields = await JsonModel.objects.all(text_field__isnull=False)
        assert len(non_null_text_fields) == 0
        non_null_json_fields = await JsonModel.objects.all(json_field__isnull=False)
        assert len(non_null_json_fields) == 0
        non_null_json_fields = await JsonModel.objects.all(json_not_null__isnull=False)
        assert len(non_null_json_fields) == 1
