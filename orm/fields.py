import datetime
import decimal
from typing import Optional, List

import pydantic
import sqlalchemy

from orm.exceptions import ModelDefinitionError
from orm.relations import Relationship


class BaseField:
    __type__ = None

    def __init__(self, *args, **kwargs) -> None:
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
        self.autoincrement = kwargs.pop('autoincrement', self.primary_key and self.__type__ == int)

        self.nullable = kwargs.pop('nullable', not self.primary_key)
        self.default = kwargs.pop('default', None)
        self.server_default = kwargs.pop('server_default', None)

        self.index = kwargs.pop('index', None)
        self.unique = kwargs.pop('unique', None)

        self.pydantic_only = kwargs.pop('pydantic_only', False)
        if self.pydantic_only and self.primary_key:
            raise ModelDefinitionError('Primary key column cannot be pydantic only.')

    @property
    def is_required(self):
        return not self.nullable and not self.has_default and not self.is_auto_primary_key

    @property
    def default_value(self):
        default = self.default if self.default is not None else self.server_default
        return default() if callable(default) else default

    @property
    def has_default(self):
        return self.default is not None or self.server_default is not None

    @property
    def is_auto_primary_key(self):
        if self.primary_key:
            return self.autoincrement
        return False

    def get_column(self, name: str = None) -> sqlalchemy.Column:
        self.name = self.name or name
        constraints = self.get_constraints()
        return sqlalchemy.Column(
            self.name,
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

    def get_constraints(self) -> Optional[List]:
        return []

    def expand_relationship(self, value, parent):
        return value


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


class ForeignKey(BaseField):
    def __init__(self, to, related_name: str = None, nullable: bool = False):
        super().__init__(nullable=nullable)
        self.related_name = related_name
        self.to = to

    @property
    def __type__(self):
        return self.to.__pydantic_model__

    def get_constraints(self):
        fk_string = self.to.__tablename__ + "." + self.to.__pkname__
        return [sqlalchemy.schema.ForeignKey(fk_string)]

    def get_column_type(self):
        to_column = self.to.__model_fields__[self.to.__pkname__]
        return to_column.get_column_type()

    def expand_relationship(self, value, child):
        if isinstance(value, self.to):
            model = value
        elif isinstance(value, dict):
            model = self.to(**value)
        else:
            model = self.to(**{self.to.__pkname__: value})

        child_model_name = self.related_name or child.__class__.__name__.lower() + 's'
        model._orm_relationship_manager.add(
            Relationship(name=child_model_name, child=child, parent=model, fk_side='child'))
        model.__fields__[child_model_name] = pydantic.fields.ModelField(name=child_model_name,
                                                                        type_=child.__pydantic_model__,
                                                                        model_config=child.__pydantic_model__.__config__,
                                                                        class_validators=child.__pydantic_model__.__validators__)
        return model
