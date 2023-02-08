# type: ignore
import asyncio
import datetime
import decimal

import databases
import pydantic
import pytest
import pytest_asyncio
import sqlalchemy
import typing

import ormar
from ormar.exceptions import ModelDefinitionError
from ormar.models import Model
from tests.settings import DATABASE_URL

metadata = sqlalchemy.MetaData()

database = databases.Database(DATABASE_URL, force_rollback=True)


class ExampleModel(Model):
    class Meta:
        tablename = "example"
        metadata = metadata
        database = database

    test: int = ormar.Integer(primary_key=True)
    test_string: str = ormar.String(max_length=250)
    test_text: str = ormar.Text(default="")
    test_bool: bool = ormar.Boolean(nullable=False)
    test_float = ormar.Float(nullable=True)
    test_datetime = ormar.DateTime(default=datetime.datetime.now)
    test_date = ormar.Date(default=datetime.date.today)
    test_time = ormar.Time(default=datetime.time)
    test_json = ormar.JSON(default={})
    test_bigint: int = ormar.BigInteger(default=0)
    test_smallint: int = ormar.SmallInteger(default=0)
    test_decimal = ormar.Decimal(scale=2, precision=10)
    test_decimal2 = ormar.Decimal(max_digits=10, decimal_places=2)


fields_to_check = [
    "test",
    "test_text",
    "test_string",
    "test_datetime",
    "test_date",
    "test_text",
    "test_float",
    "test_bigint",
    "test_json",
]


class ExampleModel2(Model):
    class Meta:
        tablename = "examples"
        metadata = metadata
        database = database

    test: int = ormar.Integer(primary_key=True)
    test_string: str = ormar.String(max_length=250)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.fixture()
def example():
    return ExampleModel(
        pk=1,
        test_string="test",
        test_bool=True,
        test_decimal=decimal.Decimal(3.5),
        test_decimal2=decimal.Decimal(5.5),
    )


def test_not_nullable_field_is_required():
    with pytest.raises(pydantic.error_wrappers.ValidationError):
        ExampleModel(test=1, test_string="test")


def test_model_attribute_access(example):
    assert example.test == 1
    assert example.test_string == "test"
    assert example.test_datetime.year == datetime.datetime.now().year
    assert example.test_date == datetime.date.today()
    assert example.test_text == ""
    assert example.test_float is None
    assert example.test_bigint == 0
    assert example.test_json == {}
    assert example.test_decimal == 3.5
    assert example.test_decimal2 == 5.5

    example.test = 12
    assert example.test == 12

    example._orm_saved = True
    assert example._orm_saved


def test_model_attribute_json_access(example):
    example.test_json = dict(aa=12)
    assert example.test_json == dict(aa=12)


def test_missing_metadata():
    with pytest.raises(ModelDefinitionError):

        class JsonSample2(ormar.Model):
            class Meta:
                tablename = "jsons2"
                database = database

            id: int = ormar.Integer(primary_key=True)
            test_json = ormar.JSON(nullable=True)


def test_missing_database():
    with pytest.raises(ModelDefinitionError):

        class JsonSample3(ormar.Model):
            class Meta:
                tablename = "jsons3"

            id: int = ormar.Integer(primary_key=True)
            test_json = ormar.JSON(nullable=True)


def test_non_existing_attr(example):
    with pytest.raises(ValueError):
        example.new_attr = 12


def test_primary_key_access_and_setting(example):
    assert example.pk == 1
    example.pk = 2

    assert example.pk == 2
    assert example.test == 2


def test_pydantic_model_is_created(example):
    assert issubclass(example.__class__, pydantic.BaseModel)
    assert all([field in example.__fields__ for field in fields_to_check])
    assert example.test == 1


def test_sqlalchemy_table_is_created(example):
    assert issubclass(example.Meta.table.__class__, sqlalchemy.Table)
    assert all([field in example.Meta.table.columns for field in fields_to_check])


@typing.no_type_check
def test_no_pk_in_model_definition():
    with pytest.raises(ModelDefinitionError):  # type: ignore

        class ExampleModel2(Model):  # type: ignore
            class Meta:
                tablename = "example2"
                database = database
                metadata = metadata

            test_string: str = ormar.String(max_length=250)  # type: ignore


@typing.no_type_check
def test_two_pks_in_model_definition():
    with pytest.raises(ModelDefinitionError):

        @typing.no_type_check
        class ExampleModel2(Model):
            class Meta:
                tablename = "example3"
                database = database
                metadata = metadata

            id: int = ormar.Integer(primary_key=True)
            test_string: str = ormar.String(max_length=250, primary_key=True)


@typing.no_type_check
def test_setting_pk_column_as_pydantic_only_in_model_definition():
    with pytest.raises(ModelDefinitionError):

        class ExampleModel2(Model):
            class Meta:
                tablename = "example4"
                database = database
                metadata = metadata

            test: int = ormar.Integer(primary_key=True, pydantic_only=True)


@typing.no_type_check
def test_decimal_error_in_model_definition():
    with pytest.raises(ModelDefinitionError):

        class ExampleModel2(Model):
            class Meta:
                tablename = "example5"
                database = database
                metadata = metadata

            test: decimal.Decimal = ormar.Decimal(primary_key=True)


@typing.no_type_check
def test_binary_error_without_length_model_definition():
    with pytest.raises(ModelDefinitionError):

        class ExampleModel2(Model):
            class Meta:
                tablename = "example6"
                database = database
                metadata = metadata

            test: bytes = ormar.LargeBinary(primary_key=True, max_length=-1)


@typing.no_type_check
def test_string_error_in_model_definition():
    with pytest.raises(ModelDefinitionError):

        class ExampleModel2(Model):
            class Meta:
                tablename = "example6"
                database = database
                metadata = metadata

            test: str = ormar.String(primary_key=True, max_length=0)


@typing.no_type_check
def test_json_conversion_in_model():
    with pytest.raises(pydantic.ValidationError):
        ExampleModel(
            test_json=datetime.datetime.now(),
            test=1,
            test_string="test",
            test_bool=True,
        )


def test_foreign_key_index():

    class User(ormar.Model):
        class Meta:
            tablename = "users"
            database = database
            metadata = metadata

        id: int = ormar.Integer(primary_key=True)

    class Account(ormar.Model):
        class Meta:
            tablename = "accounts"
            database = database
            metadata = metadata
        id: int = ormar.Integer(primary_key=True)
        user: User = ormar.ForeignKey(User, index=False)

    class Purchase(ormar.Model):
        class Meta:
            tablename = "purchases"
            database = database
            metadata = metadata

        id: int = ormar.Integer(primary_key=True)
        user: User = ormar.ForeignKey(User, index=True)

    assert Account.Meta.table.columns.user.index is False  # type: ignore
    assert Purchase.Meta.table.columns.user.index is True  # type: ignore
