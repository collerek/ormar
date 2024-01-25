from typing import Optional

import databases
import ormar
import pytest
import sqlalchemy

from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class Department(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Course(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    completed: bool = ormar.Boolean(default=False)
    department: Optional[Department] = ormar.ForeignKey(Department)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_adding_relation_to_reverse_saves_the_child():
    async with database:
        department = await Department(name="Science").save()
        course = Course(name="Math", completed=False)

        await department.courses.add(course)
        assert course.pk is not None
        assert course.department == department
        assert department.courses[0] == course
