import datetime
from enum import Enum
from typing import Optional

import ormar
import pydantic
import pytest
from ormar import ModelDefinitionError

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config(force_rollback=True)


def time():
    return datetime.datetime.now().time()


class MyEnum(Enum):
    SMALL = 1
    BIG = 2


class Example(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="example")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=200, default="aaa")
    created: datetime.datetime = ormar.DateTime(default=datetime.datetime.now)
    created_day: datetime.date = ormar.Date(default=datetime.date.today)
    created_time: datetime.time = ormar.Time(default=time)
    description: Optional[str] = ormar.Text(nullable=True)
    value: Optional[float] = ormar.Float(nullable=True)
    data: pydantic.Json = ormar.JSON(default={})
    size: MyEnum = ormar.Enum(enum_class=MyEnum, default=MyEnum.SMALL)


class EnumExample(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="enum_example")

    id: int = ormar.Integer(primary_key=True)
    size: MyEnum = ormar.Enum(enum_class=MyEnum, default=MyEnum.SMALL)


create_test_database = init_tests(base_ormar_config)


def test_proper_enum_column_type():
    assert Example.model_fields["size"].__type__ == MyEnum


def test_accepts_only_proper_enums():
    class WrongEnum(Enum):
        A = 1
        B = 2

    with pytest.raises(pydantic.ValidationError):
        Example(size=WrongEnum.A)


@pytest.mark.asyncio
async def test_enum_bulk_operations():
    async with base_ormar_config.database:
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
    async with base_ormar_config.database:
        examples = [EnumExample(), EnumExample(size=MyEnum.BIG)]
        await EnumExample.objects.bulk_create(examples)

        check = await EnumExample.objects.all(size=MyEnum.SMALL)
        assert len(check) == 1

        check = await EnumExample.objects.all(size=MyEnum.BIG)
        assert len(check) == 1


@pytest.mark.asyncio
async def test_model_crud():
    async with base_ormar_config.database:
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
async def test_invalid_enum_field() -> None:
    async with base_ormar_config.database:
        with pytest.raises(ModelDefinitionError):

            class Example2(ormar.Model):
                ormar_config = base_ormar_config.copy(tablename="example2")

                id: int = ormar.Integer(primary_key=True)
                size: MyEnum = ormar.Enum(enum_class=[])  # type: ignore
