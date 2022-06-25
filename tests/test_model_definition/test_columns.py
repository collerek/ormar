import datetime
from enum import Enum

import databases
import pydantic
import pytest
import sqlalchemy

import ormar
from ormar import ModelDefinitionError
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


def time():
    return datetime.datetime.now().time()


class MyEnum(Enum):
    SMALL = 1
    BIG = 2


class Example(ormar.Model):
    class Meta:
        tablename = "example"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=200, default="aaa")
    created: datetime.datetime = ormar.DateTime(default=datetime.datetime.now)
    created_day: datetime.date = ormar.Date(default=datetime.date.today)
    created_time: datetime.time = ormar.Time(default=time)
    description: str = ormar.Text(nullable=True)
    value: float = ormar.Float(nullable=True)
    data: pydantic.Json = ormar.JSON(default={})
    size: MyEnum = ormar.Enum(enum_class=MyEnum, default=MyEnum.SMALL)


class EnumExample(ormar.Model):
    class Meta:
        tablename = "enum_example"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    size: MyEnum = ormar.Enum(enum_class=MyEnum, default=MyEnum.SMALL)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


def test_proper_enum_column_type():
    assert Example.__fields__["size"].type_ == MyEnum


def test_accepts_only_proper_enums():
    class WrongEnum(Enum):
        A = 1
        B = 2

    with pytest.raises(pydantic.ValidationError):
        Example(size=WrongEnum.A)


@pytest.mark.asyncio
async def test_enum_bulk_operations():
    async with database:
        examples = [EnumExample(), EnumExample()]
        await EnumExample.objects.bulk_create(examples)

        check = await EnumExample.objects.all()
        assert all(x.size == MyEnum.SMALL for x in check)

        for x in check:
            x.size = MyEnum.BIG

        await EnumExample.objects.bulk_update(check)
        check2 = await EnumExample.objects.all()
        assert all(x.size == MyEnum.BIG for x in check2)


@pytest.mark.asyncio
async def test_enum_filter():
    async with database:
        examples = [EnumExample(), EnumExample(size=MyEnum.BIG)]
        await EnumExample.objects.bulk_create(examples)

        check = await EnumExample.objects.all(size=MyEnum.SMALL)
        assert len(check) == 1

        check = await EnumExample.objects.all(size=MyEnum.BIG)
        assert len(check) == 1


@pytest.mark.asyncio
async def test_model_crud():
    async with database:
        example = Example()
        await example.save()

        await example.load()
        assert example.created.year == datetime.datetime.now().year
        assert example.created_day == datetime.date.today()
        assert example.description is None
        assert example.value is None
        assert example.data == {}
        assert example.size == MyEnum.SMALL

        await example.update(data={"foo": 123}, value=123.456, size=MyEnum.BIG)
        await example.load()
        assert example.value == 123.456
        assert example.data == {"foo": 123}
        assert example.size == MyEnum.BIG

        await example.update(data={"foo": 123}, value=123.456)
        await example.load()
        assert example.value == 123.456
        assert example.data == {"foo": 123}

        await example.delete()

@pytest.mark.asyncio
async def test_enum_schema():
    Example.get_pydantic().schema_json()



@pytest.mark.asyncio
async def test_invalid_enum_field():
    async with database:
        with pytest.raises(ModelDefinitionError):

            class Example2(ormar.Model):
                class Meta:
                    tablename = "example"
                    metadata = metadata
                    database = database

                id: int = ormar.Integer(primary_key=True)
                size: MyEnum = ormar.Enum(enum_class=[])
