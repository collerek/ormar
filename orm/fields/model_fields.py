import datetime
import decimal

import sqlalchemy
from pydantic import Json

from orm.fields.base import BaseField  # noqa I101
from orm.fields.required_decorator import RequiredParams


@RequiredParams("length")
class String(BaseField):
    __type__ = str

    def get_column_type(self) -> sqlalchemy.Column:
        return sqlalchemy.String(self.length)


class Integer(BaseField):
    __type__ = int

    def get_column_type(self) -> sqlalchemy.Column:
        return sqlalchemy.Integer()


class Text(BaseField):
    __type__ = str

    def get_column_type(self) -> sqlalchemy.Column:
        return sqlalchemy.Text()


class Float(BaseField):
    __type__ = float

    def get_column_type(self) -> sqlalchemy.Column:
        return sqlalchemy.Float()


class Boolean(BaseField):
    __type__ = bool

    def get_column_type(self) -> sqlalchemy.Column:
        return sqlalchemy.Boolean()


class DateTime(BaseField):
    __type__ = datetime.datetime

    def get_column_type(self) -> sqlalchemy.Column:
        return sqlalchemy.DateTime()


class Date(BaseField):
    __type__ = datetime.date

    def get_column_type(self) -> sqlalchemy.Column:
        return sqlalchemy.Date()


class Time(BaseField):
    __type__ = datetime.time

    def get_column_type(self) -> sqlalchemy.Column:
        return sqlalchemy.Time()


class JSON(BaseField):
    __type__ = Json

    def get_column_type(self) -> sqlalchemy.Column:
        return sqlalchemy.JSON()


class BigInteger(BaseField):
    __type__ = int

    def get_column_type(self) -> sqlalchemy.Column:
        return sqlalchemy.BigInteger()


@RequiredParams("length", "precision")
class Decimal(BaseField):
    __type__ = decimal.Decimal

    def get_column_type(self) -> sqlalchemy.Column:
        return sqlalchemy.DECIMAL(self.length, self.precision)
