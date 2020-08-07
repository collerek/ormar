import databases
import pytest
import sqlalchemy

import orm
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class SchoolClass(orm.Model):
    __tablename__ = "schoolclasses"
    __metadata__ = metadata
    __database__ = database

    id = orm.Integer(primary_key=True)
    name = orm.String(length=100)


class Category(orm.Model):
    __tablename__ = "categories"
    __metadata__ = metadata
    __database__ = database

    id = orm.Integer(primary_key=True)
    name = orm.String(length=100)


class Student(orm.Model):
    __tablename__ = "students"
    __metadata__ = metadata
    __database__ = database

    id = orm.Integer(primary_key=True)
    name = orm.String(length=100)
    schoolclass = orm.ForeignKey(SchoolClass)
    category = orm.ForeignKey(Category, nullable=True)


class Teacher(orm.Model):
    __tablename__ = "teachers"
    __metadata__ = metadata
    __database__ = database

    id = orm.Integer(primary_key=True)
    name = orm.String(length=100)
    schoolclass = orm.ForeignKey(SchoolClass)
    category = orm.ForeignKey(Category, nullable=True)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_model_multiple_instances_of_same_table_in_schema():
    async with database:
        class1 = await SchoolClass.objects.create(name="Math")
        category = await Category.objects.create(name="Foreign")
        category2 = await Category.objects.create(name="Domestic")
        await Student.objects.create(name="Jane", category=category, schoolclass=class1)
        await Teacher.objects.create(name="Joe", category=category2, schoolclass=class1)

        classes = await SchoolClass.objects.select_related(['teachers', 'students']).all()
        assert classes[0].name == 'Math'
        assert classes[0].students[0].name == 'Jane'

        # related fields of main model are only populated by pk
        # but you can load them anytime
        assert classes[0].students[0].schoolclass.name is None
        await classes[0].students[0].schoolclass.load()
        assert classes[0].students[0].schoolclass.name == 'Math'


@pytest.mark.asyncio
async def test_right_tables_join():
    async with database:
        class1 = await SchoolClass.objects.create(name="Math")
        category = await Category.objects.create(name="Foreign")
        category2 = await Category.objects.create(name="Domestic")
        await Student.objects.create(name="Jane", category=category, schoolclass=class1)
        await Teacher.objects.create(name="Joe", category=category2, schoolclass=class1)

        classes = await SchoolClass.objects.select_related(['teachers__category', 'students']).all()
        assert classes[0].name == 'Math'
        assert classes[0].students[0].name == 'Jane'
        breakpoint()
        assert classes[0].teachers[0].category.name == 'Domestic'
