from typing import Optional

import ormar
import pytest

from tests.settings import create_config
from tests.lifespan import init_tests


base_ormar_config = create_config()


class Department(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Course(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    completed: bool = ormar.Boolean(default=False)
    department: Optional[Department] = ormar.ForeignKey(Department)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_adding_relation_to_reverse_saves_the_child():
    async with base_ormar_config.database:
        department = await Department(name="Science").save()
        course = Course(name="Math", completed=False)

        await department.courses.add(course)
        assert course.pk is not None
        assert course.department == department
        assert department.courses[0] == course
