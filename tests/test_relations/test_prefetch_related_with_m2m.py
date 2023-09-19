from typing import Optional

import databases
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    database = database
    metadata = metadata


class Author(ormar.Model):
    class Meta(BaseMeta):
        tablename = "authors"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=256)


class BookAuthor(ormar.Model):
    class Meta(BaseMeta):
        tablename = 'book_authors'

    id: int = ormar.Integer(primary_key=True)


class BookCoAuthor(ormar.Model):
    class Meta(BaseMeta):
        tablename = 'book_co_authors'

    id: int = ormar.Integer(primary_key=True)


class Book(ormar.Model):
    class Meta(BaseMeta):
        tablename = "books"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=256)
    description: Optional[str] = ormar.String(max_length=256, nullable=True)
    authors: Optional[list[Author]] = ormar.ManyToMany(
        Author, related_name='author_books', through=BookAuthor
    )
    co_authors: Optional[list[Author]] = ormar.ManyToMany(
        Author, related_name='co_author_books', through=BookCoAuthor
    )

@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_db():
    async with database:
        for i in range(6):
            await Author.objects.create(name=f"Name_{i}")

        book = await Book.objects.create(name="Book_1", description="Description_1")
        for i in range(1, 3):
            await book.authors.add(await Author.objects.get(id=i))
        for i in range(3, 6):
            await book.co_authors.add(await Author.objects.get(id=i))

        print('')
        prefetch_result = await Book.objects.prefetch_related(['authors', 'co_authors']).all()
        import json
        prefetch_dict_result = [x.dict() for x in prefetch_result if x.id == 1][0]
        print(json.dumps(prefetch_dict_result, indent=4))

        select_result = await Book.objects.select_related(['authors', 'co_authors']).all()

        import json
        select_dict_result = [
            x.dict(
                exclude={'authors': {'bookauthor': ...}, 'co_authors': {'bookcoauthor': ...}}
            ) for x in select_result if x.id == 1
        ][0]
        print(json.dumps(select_dict_result, indent=4))
        assert prefetch_dict_result == select_dict_result
