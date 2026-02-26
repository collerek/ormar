import asyncio

import sqlalchemy
from examples import create_drop_database

import ormar
from ormar import DatabaseConnection

DATABASE_URL = "sqlite+aiosqlite:///queries_docs002.db"

database = DatabaseConnection(DATABASE_URL)
metadata = sqlalchemy.MetaData()

ormar_base_config = ormar.OrmarConfig(
    database=database,
    metadata=metadata,
)


class Book(ormar.Model):
    ormar_config = ormar_base_config.copy(
        tablename="books",
    )

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

    await Book.objects.update(each=True, genre="Fiction")
    all_books = await Book.objects.filter(genre="Fiction").all()
    assert len(all_books) == 3


asyncio.run(run_query())
