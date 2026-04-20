from typing import Optional

import pytest

import ormar
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config(force_rollback=True)


class SchoolClass(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="app.schoolclasses")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Category(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="app.categories")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Student(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="app.students")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    gpa: float = ormar.Float()
    schoolclass: Optional[SchoolClass] = ormar.ForeignKey(
        SchoolClass, related_name="students"
    )
    category: Optional[Category] = ormar.ForeignKey(
        Category, nullable=True, related_name="students"
    )


create_test_database = init_tests(base_ormar_config)


async def create_data():
    class1 = await SchoolClass.objects.create(name="Math")
    class2 = await SchoolClass.objects.create(name="Logic")
    category = await Category.objects.create(name="Foreign")
    category2 = await Category.objects.create(name="Domestic")
    await Student.objects.create(
        name="Jane", category=category, schoolclass=class1, gpa=3.2
    )
    await Student.objects.create(
        name="Judy", category=category2, schoolclass=class1, gpa=2.6
    )
    await Student.objects.create(
        name="Jack", category=category2, schoolclass=class2, gpa=3.8
    )


@pytest.mark.asyncio
async def test_quotes_left_join():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            await create_data()
            students = await Student.objects.filter(
                (Student.schoolclass.name == "Math")
                | (Student.category.name == "Foreign")
            ).all()
            for student in students:
                assert (
                    student.schoolclass.name == "Math"
                    or student.category.name == "Foreign"
                )


@pytest.mark.asyncio
async def test_quotes_reverse_join():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            await create_data()
            schoolclasses = await SchoolClass.objects.filter(students__gpa__gt=3).all()
            for schoolclass in schoolclasses:
                for student in schoolclass.students:
                    assert student.gpa > 3


@pytest.mark.asyncio
async def test_quotes_deep_join():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            await create_data()
            schoolclasses = await SchoolClass.objects.filter(
                students__category__name="Domestic"
            ).all()
            for schoolclass in schoolclasses:
                for student in schoolclass.students:
                    assert student.category.name == "Domestic"
