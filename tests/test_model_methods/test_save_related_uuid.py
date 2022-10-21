import uuid
from typing import Optional

import databases
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Department(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4)
    department_name: str = ormar.String(max_length=100)


class Course(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4)
    course_name: str = ormar.String(max_length=100)
    completed: bool = ormar.Boolean()
    department: Optional[Department] = ormar.ForeignKey(Department)


class Student(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4)
    name: str = ormar.String(max_length=100)
    courses = ormar.ManyToMany(Course)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_uuid_pk_in_save_related():
    async with database:
        to_save = {
            "department_name": "Ormar",
            "courses": [
                {
                    "course_name": "basic1",
                    "completed": True,
                    "students": [{"name": "Abi"}, {"name": "Jack"}],
                },
                {
                    "course_name": "basic2",
                    "completed": True,
                    "students": [{"name": "Kate"}, {"name": "Miranda"}],
                },
            ],
        }
        department = Department(**to_save)
        await department.save_related(follow=True, save_all=True)
        department_check = (
            await Department.objects.select_all(follow=True)
            .order_by(Department.courses.students.name.asc())
            .get()
        )
        to_exclude = {
            "id": ...,
            "courses": {"id": ..., "students": {"id", "studentcourse"}},
        }
        assert department_check.dict(exclude=to_exclude) == to_save
