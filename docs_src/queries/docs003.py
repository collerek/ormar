import asyncio

import ormar
import sqlalchemy
from examples import create_drop_database
from ormar import DatabaseConnection

DATABASE_URL = "sqlite+aiosqlite:///queries_docs003.db"

database = DatabaseConnection(DATABASE_URL)
metadata = sqlalchemy.MetaData()

ormar_base_config = ormar.OrmarConfig(
    database=database,
    metadata=metadata,
)


class Book(ormar.Model):
    ormar_config = ormar_base_config.copy()

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=200)
    author: str = ormar.String(max_length=100)
    genre: str = ormar.String(
        max_length=100,
        default="Fiction",
    )


@create_drop_database(base_config=ormar_base_config)
async def run_query():
    await Book.objects.create(
        title="Tom Sawyer", author="Twain, Mark", genre="Adventure"
    )
    await Book.objects.create(
        title="War and Peace", author="Tolstoy, Leo", genre="Fiction"
    )
    await Book.objects.create(
        title="Anna Karenina", author="Tolstoy, Leo", genre="Fiction"
    )

    # if not exist the instance will be persisted in db
    vol2 = await Book.objects.update_or_create(
        title="Volume II", author="Anonymous", genre="Fiction"
    )
    assert await Book.objects.count() == 4

    # if pk or pkname passed in kwargs (like id here) the object will be updated
    assert await Book.objects.update_or_create(id=vol2.id, genre="Historic")
    assert await Book.objects.count() == 4


asyncio.run(run_query())
