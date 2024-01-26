import asyncio
from typing import Optional

import databases
import ormar
import sqlalchemy
from examples import create_drop_database

DATABASE_URL = "sqlite:///test.db"

ormar_base_config = ormar.OrmarConfig(
    database=databases.Database(DATABASE_URL), metadata=sqlalchemy.MetaData()
)


class Department(ormar.Model):
    ormar_config = ormar_base_config.copy(tablename="departments")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Course(ormar.Model):
    ormar_config = ormar_base_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    completed: bool = ormar.Boolean(default=False)
    department: Optional[Department] = ormar.ForeignKey(Department)


@create_drop_database(base_config=ormar_base_config)
async def verify():
    department = await Department(name="Science").save()
    course = Course(name="Math", completed=False, department=department)
    print(department.courses[0])
    # Will produce:
    # Course(id=None,
    #        name='Math',
    #        completed=False,
    #        department=Department(id=None, name='Science'))
    await course.save()


asyncio.run(verify())
