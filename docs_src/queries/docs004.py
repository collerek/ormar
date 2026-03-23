import asyncio

import sqlalchemy
from examples import create_drop_database

import ormar
from ormar import DatabaseConnection

DATABASE_URL = "sqlite+aiosqlite:///queries_docs004.db"

database = DatabaseConnection(DATABASE_URL)
metadata = sqlalchemy.MetaData()

ormar_base_config = ormar.OrmarConfig(
    database=database,
    metadata=metadata,
)


class ToDo(ormar.Model):
    ormar_config = ormar_base_config.copy(tablename="todos")

    id: int = ormar.Integer(primary_key=True)
    text: str = ormar.String(max_length=500)
    completed = ormar.Boolean(default=False)


@create_drop_database(base_config=ormar_base_config)
async def run_query():
    # create multiple instances at once with bulk_create
    await ToDo.objects.bulk_create(
        [
            ToDo(text="Buy the groceries."),
            ToDo(text="Call Mum.", completed=True),
            ToDo(text="Send invoices.", completed=True),
        ]
    )

    todoes = await ToDo.objects.all()
    assert len(todoes) == 3


asyncio.run(run_query())
