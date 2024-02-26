import asyncio
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
        tablename = "departments"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True, autoincrement=False)
    name: str = ormar.String(max_length=100)


class SchoolClass(ormar.Model):
    class Meta:
        tablename = "schoolclasses"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    department: Optional[Department] = ormar.ForeignKey(Department, nullable=False)


class Category(ormar.Model):
    class Meta:
        tablename = "categories"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Student(ormar.Model):
    class Meta:
        tablename = "students"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    schoolclass: Optional[SchoolClass] = ormar.ForeignKey(SchoolClass)
    category: Optional[Category] = ormar.ForeignKey(Category, nullable=True)


class Teacher(ormar.Model):
    class Meta:
        tablename = "teachers"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    schoolclass: Optional[SchoolClass] = ormar.ForeignKey(SchoolClass)
    category: Optional[Category] = ormar.ForeignKey(Category, nullable=True)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


async def create_data():
    department = await Department.objects.create(id=1, name="Math Department")
    department2 = await Department.objects.create(id=2, name="Law Department")
    class1 = await SchoolClass.objects.create(name="Math", department=department)
    class2 = await SchoolClass.objects.create(name="Logic", department=department2)
    category = await Category.objects.create(name="Foreign")
    category2 = await Category.objects.create(name="Domestic")
    await Student.objects.create(name="Jane", category=category, schoolclass=class1)
    await Student.objects.create(name="Judy", category=category2, schoolclass=class1)
    await Student.objects.create(name="Jack", category=category2, schoolclass=class2)
    await Teacher.objects.create(name="Joe", category=category2, schoolclass=class1)


@pytest.mark.asyncio
async def test_model_multiple_instances_of_same_table_in_schema():
    async with database:
        async with database.transaction(force_rollback=True):
            await create_data()
            classes = await SchoolClass.objects.select_related(
                ["teachers__category", "students__schoolclass"]
            ).all()
            assert classes[0].name == "Math"
            assert classes[0].students[0].name == "Jane"

            assert len(classes[0].dict().get("students")) == 2

            # since it's going from schoolclass => teacher => schoolclass (same class) department is already populated
            assert classes[0].students[0].schoolclass.name == "Math"
            assert classes[0].students[0].schoolclass.department.name is None
            await classes[0].students[0].schoolclass.department.load()
            assert (
                classes[0].students[0].schoolclass.department.name == "Math Department"
            )

            await classes[1].students[0].schoolclass.department.load()
            assert (
                classes[1].students[0].schoolclass.department.name == "Law Department"
            )


@pytest.mark.asyncio
async def test_right_tables_join():
    async with database:
        async with database.transaction(force_rollback=True):
            await create_data()
            classes = await SchoolClass.objects.select_related(
                ["teachers__category", "students"]
            ).all()
            assert classes[0].teachers[0].category.name == "Domestic"

            assert classes[0].students[0].category.name is None
            await classes[0].students[0].category.load()
            assert classes[0].students[0].category.name == "Foreign"


@pytest.mark.asyncio
async def test_multiple_reverse_related_objects():
    async with database:
        async with database.transaction(force_rollback=True):
            await create_data()
            classes = await SchoolClass.objects.select_related(
                ["teachers__category", "students__category"]
            ).all()
            assert classes[0].name == "Math"
            assert classes[0].students[1].name == "Judy"
            assert classes[0].students[0].category.name == "Foreign"
            assert classes[0].students[1].category.name == "Domestic"
            assert classes[0].teachers[0].category.name == "Domestic"
