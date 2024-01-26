import asyncio

import databases
import ormar
import sqlalchemy
from examples import create_drop_database

DATABASE_URL = "sqlite:///test.db"

ormar_base_config = ormar.OrmarConfig(
    database=databases.Database(DATABASE_URL), metadata=sqlalchemy.MetaData()
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
