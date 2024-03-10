from typing import Optional

import databases
import ormar
import pytest
import sqlalchemy

from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class SchoolClass(ormar.Model):
    class Meta:
        tablename = "app.schoolclasses"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Category(ormar.Model):
    class Meta:
        tablename = "app.categories"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Student(ormar.Model):
    class Meta:
        tablename = "app.students"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    gpa: float = ormar.Float()
    schoolclass: Optional[SchoolClass] = ormar.ForeignKey(
        SchoolClass, related_name="students"
    )
    category: Optional[Category] = ormar.ForeignKey(
        Category, nullable=True, related_name="students"
    )


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


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
    async with database:
        async with database.transaction(force_rollback=True):
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
    async with database:
        async with database.transaction(force_rollback=True):
            await create_data()
            schoolclasses = await SchoolClass.objects.filter(students__gpa__gt=3).all()
            for schoolclass in schoolclasses:
                for student in schoolclass.students:
                    assert student.gpa > 3


@pytest.mark.asyncio
async def test_quotes_deep_join():
    async with database:
        async with database.transaction(force_rollback=True):
            await create_data()
            schoolclasses = await SchoolClass.objects.filter(
                students__category__name="Domestic"
            ).all()
            for schoolclass in schoolclasses:
                for student in schoolclass.students:
                    assert student.category.name == "Domestic"
