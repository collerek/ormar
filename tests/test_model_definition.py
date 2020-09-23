import datetime
import decimal

import pydantic
import pytest
import sqlalchemy

import ormar.fields as fields
from ormar.exceptions import ModelDefinitionError
from ormar.models import Model

metadata = sqlalchemy.MetaData()


class ExampleModel(Model):
    class Meta:
        tablename = "example"
        metadata = metadata

    test: fields.Integer(primary_key=True)
    test_string: fields.String(max_length=250)
    test_text: fields.Text(default="")
    test_bool: fields.Boolean(nullable=False)
    test_float: fields.Float() = None
    test_datetime: fields.DateTime(default=datetime.datetime.now)
    test_date: fields.Date(default=datetime.date.today)
    test_time: fields.Time(default=datetime.time)
    test_json: fields.JSON(default={})
    test_bigint: fields.BigInteger(default=0)
    test_decimal: fields.Decimal(scale=10, precision=2)
    test_decimal2: fields.Decimal(max_digits=10, decimal_places=2)


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
        tablename = "example2"
        metadata = metadata

    test: fields.Integer(primary_key=True)
    test_string: fields.String(max_length=250)


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


def test_no_pk_in_model_definition():
    with pytest.raises(ModelDefinitionError):

        class ExampleModel2(Model):
            class Meta:
                tablename = "example3"
                metadata = metadata

            test_string: fields.String(max_length=250)


def test_two_pks_in_model_definition():
    with pytest.raises(ModelDefinitionError):

        class ExampleModel2(Model):
            class Meta:
                tablename = "example3"
                metadata = metadata

            id: fields.Integer(primary_key=True)
            test_string: fields.String(max_length=250, primary_key=True)


def test_setting_pk_column_as_pydantic_only_in_model_definition():
    with pytest.raises(ModelDefinitionError):

        class ExampleModel2(Model):
            class Meta:
                tablename = "example4"
                metadata = metadata

            test: fields.Integer(primary_key=True, pydantic_only=True)


def test_decimal_error_in_model_definition():
    with pytest.raises(ModelDefinitionError):

        class ExampleModel2(Model):
            class Meta:
                tablename = "example5"
                metadata = metadata

            test: fields.Decimal(primary_key=True)


def test_string_error_in_model_definition():
    with pytest.raises(ModelDefinitionError):

        class ExampleModel2(Model):
            class Meta:
                tablename = "example6"
                metadata = metadata

            test: fields.String(primary_key=True)


def test_json_conversion_in_model():
    with pytest.raises(pydantic.ValidationError):
        ExampleModel(
            test_json=datetime.datetime.now(),
            test=1,
            test_string="test",
            test_bool=True,
        )
