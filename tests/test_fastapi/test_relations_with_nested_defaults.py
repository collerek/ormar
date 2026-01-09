from typing import Optional

import ormar
import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from tests.lifespan import init_tests, lifespan
from tests.settings import create_config

base_ormar_config = create_config()
app = FastAPI(lifespan=lifespan(base_ormar_config))


class Country(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="countries")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, default="Poland")


class Author(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="authors")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    rating: int = ormar.Integer(default=0)
    country: Optional[Country] = ormar.ForeignKey(Country)


class Book(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="books")

    id: int = ormar.Integer(primary_key=True)
    author: Optional[Author] = ormar.ForeignKey(Author)
    title: str = ormar.String(max_length=100)
    year: int = ormar.Integer(nullable=True)


create_test_database = init_tests(base_ormar_config)


@pytest_asyncio.fixture
async def sample_data():
    async with base_ormar_config.database:
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


@pytest.mark.asyncio
async def test_related_with_defaults(sample_data):
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    async with client as client, LifespanManager(app):
        response = await client.get("/books/1")
        assert response.json() == {
            "author": {
                "books": [
                    {
                        "author": {"id": 1},
                        "id": 1,
                        "title": "Bug caused by default value",
                        "year": 2021,
                    }
                ],
                "id": 1,
            },
            "id": 1,
            "title": "Bug caused by default value",
            "year": 2021,
        }

        response = await client.get("/books_with_author/1")
        assert response.json() == {
            "author": {
                "books": [
                    {
                        "author": {"id": 1},
                        "id": 1,
                        "title": "Bug caused by default value",
                        "year": 2021,
                    }
                ],
                "country": {
                    "authors": [
                        {
                            "books": [
                                {
                                    "author": {"id": 1},
                                    "id": 1,
                                    "title": "Bug caused by " "default value",
                                    "year": 2021,
                                }
                            ],
                            "country": {"id": 1},
                            "id": 1,
                            "name": "bug",
                            "rating": 5,
                        }
                    ],
                    "id": 1,
                },
                "id": 1,
                "name": "bug",
                "rating": 5,
            },
            "id": 1,
            "title": "Bug caused by default value",
            "year": 2021,
        }
