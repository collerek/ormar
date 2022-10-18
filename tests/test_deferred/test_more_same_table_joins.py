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


class Category(ormar.Model):
    class Meta:
        tablename = "categories"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    department: Optional[Department] = ormar.ForeignKey(Department, nullable=False)


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
    class1 = await SchoolClass.objects.create(name="Math")
    class2 = await SchoolClass.objects.create(name="Logic")
    category = await Category.objects.create(name="Foreign", department=department)
    category2 = await Category.objects.create(name="Domestic", department=department2)
    await Student.objects.create(name="Jane", category=category, schoolclass=class1)
    await Student.objects.create(name="Judy", category=category2, schoolclass=class1)
    await Student.objects.create(name="Jack", category=category2, schoolclass=class2)
    await Teacher.objects.create(name="Joe", category=category2, schoolclass=class1)


@pytest.mark.asyncio
async def test_model_multiple_instances_of_same_table_in_schema():
    async with database:
        await create_data()
        classes = await SchoolClass.objects.select_related(
            ["teachers__category__department", "students__category__department"]
        ).all()
        assert classes[0].name == "Math"
        assert classes[0].students[0].name == "Jane"
        assert len(classes[0].dict().get("students")) == 2
        assert classes[0].teachers[0].category.department.name == "Law Department"
        assert classes[0].students[0].category.department.name == "Math Department"


@pytest.mark.asyncio
async def test_load_all_multiple_instances_of_same_table_in_schema():
    async with database:
        await create_data()
        math_class = await SchoolClass.objects.get(name="Math")
        assert math_class.name == "Math"

        await math_class.load_all(follow=True)
        assert math_class.students[0].name == "Jane"
        assert len(math_class.dict().get("students")) == 2
        assert math_class.teachers[0].category.department.name == "Law Department"
        assert math_class.students[0].category.department.name == "Math Department"


@pytest.mark.asyncio
async def test_filter_groups_with_instances_of_same_table_in_schema():
    async with database:
        await create_data()
        math_class = (
            await SchoolClass.objects.select_related(
                ["teachers__category__department", "students__category__department"]
            )
            .filter(
                ormar.or_(
                    students__name="Jane",
                    teachers__category__name="Domestic",
                    students__category__name="Foreign",
                )
            )
            .get(name="Math")
        )
        assert math_class.name == "Math"
        assert math_class.students[0].name == "Jane"
        assert len(math_class.dict().get("students")) == 2
        assert math_class.teachers[0].category.department.name == "Law Department"
        assert math_class.students[0].category.department.name == "Math Department"

        classes = (
            await SchoolClass.objects.select_related(
                ["students__category__department", "teachers__category__department"]
            )
            .filter(
                ormar.and_(
                    ormar.or_(
                        students__name="Jane", students__category__name="Foreign"
                    ),
                    teachers__category__department__name="Law Department",
                )
            )
            .all()
        )
        assert len(classes) == 1
        assert classes[0].teachers[0].category.department.name == "Law Department"
        assert classes[0].students[0].category.department.name == "Math Department"
