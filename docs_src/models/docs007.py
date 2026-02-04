import asyncio

import ormar
import sqlalchemy
from examples import create_drop_database
from ormar import DatabaseConnection
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "sqlite+aiosqlite:///models_docs007.db"

database = DatabaseConnection(DATABASE_URL)
metadata = sqlalchemy.MetaData()
engine = create_async_engine(DATABASE_URL)

ormar_base_config = ormar.OrmarConfig(
    database=database,
    metadata=metadata,
    engine=engine,
)


class Course(ormar.Model):
    ormar_config = ormar_base_config.copy(tablename="courses")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    completed: bool = ormar.Boolean(default=False)


@create_drop_database(base_config=ormar_base_config)
async def run_query():
    course = Course(name="Painting for dummies", completed=False)
    await course.save()

    await Course.objects.create(name="Painting for dummies", completed=False)


asyncio.run(run_query())
