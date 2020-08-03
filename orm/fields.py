import datetime
import decimal
from typing import Any

import pydantic
import sqlalchemy

from orm.exceptions import ModelDefinitionError


class BaseField:
    __type__ = None

    def __new__(cls, *args, **kwargs):
        cls.__annotations__ = {}
        return super().__new__(cls)

    def __init__(self, *args, **kwargs):
        name = kwargs.pop('name', None)
        args = list(args)
        if args:
            if isinstance(args[0], str):
                if name is not None:
                    raise ModelDefinitionError(
                        'Column name cannot be passed positionally and as a keyword.'
                    )
                name = args.pop(0)

        self.name = name
        self.primary_key = kwargs.pop('primary_key', False)
        self.autoincrement = kwargs.pop('autoincrement', 'auto')

        self.nullable = kwargs.pop('nullable', not self.primary_key)
        self.default = kwargs.pop('default', None)
        self.server_default = kwargs.pop('server_default', None)

        self.index = kwargs.pop('index', None)
        self.unique = kwargs.pop('unique', None)

        self.pydantic_only = kwargs.pop('pydantic_only', False)
        if self.pydantic_only and self.primary_key:
            raise ModelDefinitionError('Primary key column cannot be pydantic only.')

    def get_column(self, name=None) -> sqlalchemy.Column:
        name = self.name or name
        constraints = self.get_constraints()
        return sqlalchemy.Column(
            name,
            self.get_column_type(),
            *constraints,
            primary_key=self.primary_key,
            autoincrement=self.autoincrement,
            nullable=self.nullable,
            index=self.index,
            unique=self.unique,
            default=self.default,
            server_default=self.server_default
        )

    def get_column_type(self) -> sqlalchemy.types.TypeEngine:
        raise NotImplementedError()  # pragma: no cover

    def get_constraints(self):
        return []


class String(BaseField):
    __type__ = str

    def __init__(self, *args, **kwargs):
        assert 'length' in kwargs, 'length is required'
        self.length = kwargs.pop('length')
        super().__init__(*args, **kwargs)

    def get_column_type(self):
        return sqlalchemy.String(self.length)


class Integer(BaseField):
    __type__ = int

    def get_column_type(self):
        return sqlalchemy.Integer()


class Text(BaseField):
    __type__ = str

    def get_column_type(self):
        return sqlalchemy.Text()


class Float(BaseField):
    __type__ = float

    def get_column_type(self):
        return sqlalchemy.Float()


class Boolean(BaseField):
    __type__ = bool

    def get_column_type(self):
        return sqlalchemy.Boolean()


class DateTime(BaseField):
    __type__ = datetime.datetime

    def get_column_type(self):
        return sqlalchemy.DateTime()


class Date(BaseField):
    __type__ = datetime.date

    def get_column_type(self):
        return sqlalchemy.Date()


class Time(BaseField):
    __type__ = datetime.time

    def get_column_type(self):
        return sqlalchemy.Time()


class JSON(BaseField):
    __type__ = pydantic.Json

    def get_column_type(self):
        return sqlalchemy.JSON()


class BigInteger(BaseField):
    __type__ = int

    def get_column_type(self):
        return sqlalchemy.BigInteger()


class Decimal(BaseField):
    __type__ = decimal.Decimal

    def __init__(self, *args, **kwargs):
        assert 'precision' in kwargs, 'precision is required'
        assert 'length' in kwargs, 'length is required'
        self.length = kwargs.pop('length')
        self.precision = kwargs.pop('precision')
        super().__init__(*args, **kwargs)

    def get_column_type(self):
        return sqlalchemy.DECIMAL(self.length, self.precision)
