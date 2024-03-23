import asyncio

import databases
import ormar
import sqlalchemy
from examples import create_drop_database

DATABASE_URL = "sqlite:///test.db"

ormar_base_config = ormar.OrmarConfig(
    database=databases.Database(DATABASE_URL), metadata=sqlalchemy.MetaData()
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
