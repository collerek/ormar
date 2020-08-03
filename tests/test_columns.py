import datetime

import pydantic
import pytest
import sqlalchemy

import orm.fields as fields
from orm.exceptions import ModelDefinitionError
from orm.models import Model

metadata = sqlalchemy.MetaData()


class ExampleModel(Model):
    __tablename__ = "example"
    __metadata__ = metadata
    test = fields.Integer(primary_key=True)
    test_string = fields.String(length=250)
    test_text = fields.Text(default='')
    test_bool = fields.Boolean(nullable=False)
    test_float = fields.Float()
    test_datetime = fields.DateTime(default=datetime.datetime.now)
    test_date = fields.Date(default=datetime.date.today)
    test_time = fields.Time(default=datetime.time)
    test_json = fields.JSON(default={})
    test_bigint = fields.BigInteger(default=0)
    test_decimal = fields.Decimal(length=10, precision=2)


class ExampleModel2(Model):
    __tablename__ = "example2"
    __metadata__ = metadata
    test = fields.Integer(name='test12', primary_key=True)
    test_string = fields.String('test_string2', length=250)


def test_not_nullable_field_is_required():
    with pytest.raises(pydantic.error_wrappers.ValidationError):
        ExampleModel(test=1, test_string='test')


def test_model_attribute_access():
    example = ExampleModel(test=1, test_string='test', test_bool=True)
    assert example.test == 1
    assert example.test_string == 'test'
    assert example.test_datetime.year == datetime.datetime.now().year
    assert example.test_date == datetime.date.today()
    assert example.test_text == ''
    assert example.test_float is None
    assert example.test_bigint == 0
    assert example.test_json == {}

    example.test = 12
    assert example.test == 12

    example.new_attr = 12
    assert 'new_attr' in example.__dict__


def test_primary_key_access_and_setting():
    example = ExampleModel(pk=1, test_string='test', test_bool=True)
    assert example.pk == 1
    example.pk = 2

    assert example.pk == 2
    assert example.test == 2


def test_wrong_model_definition():
    with pytest.raises(ModelDefinitionError):
        class ExampleModel2(Model):
            __tablename__ = "example3"
            __metadata__ = metadata
            test = fields.Integer(name='test12', primary_key=True)
            test_string = fields.String('test_string2', name='test_string2', length=250)
