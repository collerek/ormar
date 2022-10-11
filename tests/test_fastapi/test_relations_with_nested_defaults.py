from typing import Optional

import databases
import pytest
import pytest_asyncio
import sqlalchemy
from fastapi import FastAPI
from starlette.testclient import TestClient

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

app = FastAPI()
app.state.database = database


@app.on_event("startup")
async def startup() -> None:
    database_ = app.state.database
    if not database_.is_connected:
        await database_.connect()


@app.on_event("shutdown")
async def shutdown() -> None:
    database_ = app.state.database
    if database_.is_connected:
        await database_.disconnect()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class Country(ormar.Model):
    class Meta(BaseMeta):
        tablename = "countries"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, default="Poland")


class Author(ormar.Model):
    class Meta(BaseMeta):
        tablename = "authors"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    rating: int = ormar.Integer(default=0)
    country: Optional[Country] = ormar.ForeignKey(Country)


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
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest_asyncio.fixture
async def sample_data():
    async with database:
        country = await Country(id=1, name="USA").save()
        author = await Author(id=1, name="bug", rating=5, country=country).save()
        await Book(
            id=1, author=author, title="Bug caused by default value", year=2021
        ).save()


@app.get("/books/{book_id}", response_model=Book)
async def get_book_by_id(book_id: int):
    book = await Book.objects.get(id=book_id)
    return book


@app.get("/books_with_author/{book_id}", response_model=Book)
async def get_book_with_author_by_id(book_id: int):
    book = await Book.objects.select_related("author").get(id=book_id)
    return book


def test_related_with_defaults(sample_data):
    client = TestClient(app)
    with client as client:
        response = client.get("/books/1")
        assert response.json() == {
            "author": {"id": 1},
            "id": 1,
            "title": "Bug caused by default value",
            "year": 2021,
        }

        response = client.get("/books_with_author/1")
        assert response.json() == {
            "author": {
                "books": [
                    {"id": 1, "title": "Bug caused by default value", "year": 2021}
                ],
                "country": {"id": 1},
                "id": 1,
                "name": "bug",
                "rating": 5,
            },
            "id": 1,
            "title": "Bug caused by default value",
            "year": 2021,
        }
