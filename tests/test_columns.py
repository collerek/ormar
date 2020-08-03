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
    test2 = fields.String(length=250)


class ExampleModel2(Model):
    __tablename__ = "example2"
    __metadata__ = metadata
    test = fields.Integer(name='test12', primary_key=True)
    test2 = fields.String('test22', length=250)


def test_model_attribute_access():
    example = ExampleModel(test=1, test2='test')
    assert example.test == 1
    assert example.test2 == 'test'

    example.test = 12
    assert example.test == 12

    example.new_attr = 12
    assert 'new_attr' in example.__dict__


def test_primary_key_access_and_setting():
    example = ExampleModel(pk=1, test2='test')
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
            test2 = fields.String('test22', name='test22', length=250)
