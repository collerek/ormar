from typing import Any

import sqlalchemy
from pydantic import create_model

from orm.fields import BaseField


class ModelMetaclass(type):
    def __new__(
            mcs: type, name: str, bases: Any, attrs: dict
    ) -> type:
        new_model = super().__new__(  # type: ignore
            mcs, name, bases, attrs
        )

        if attrs.get("__abstract__"):
            return new_model

        tablename = attrs["__tablename__"]
        metadata = attrs["__metadata__"]
        pkname = None

        columns = []
        for field_name, field in new_model.__dict__.items():
            if isinstance(field, BaseField):
                if field.primary_key:
                    pkname = field_name
                columns.append(field.get_column(field_name))

        pydantic_fields = {field_name: (base_field.__type__, base_field.default or ...)
                           for field_name, base_field in new_model.__dict__.items()
                           if isinstance(base_field, BaseField)}

        new_model.__table__ = sqlalchemy.Table(tablename, metadata, *columns)
        new_model.__columns__ = columns
        new_model.__pkname__ = pkname
        new_model.__pydantic_fields__ = pydantic_fields
        new_model.__pydantic_model__ = create_model(name, **pydantic_fields)
        new_model.__fields__ = new_model.__pydantic_model__.__fields__

        return new_model


class Model(metaclass=ModelMetaclass):
    __abstract__ = True

    def __init__(self, *args, **kwargs):
        if "pk" in kwargs:
            kwargs[self.__pkname__] = kwargs.pop("pk")
        self.values = self.__pydantic_model__(**kwargs)

    def __setattr__(self, key, value):
        if key in self.__fields__:
            setattr(self.values, key, value)
        super().__setattr__(key, value)

    def __getattribute__(self, item):
        if item != '__fields__' and item in self.__fields__:
            return getattr(self.values, item)
        return super().__getattribute__(item)

    @property
    def pk(self):
        return getattr(self.values, self.__pkname__)

    @pk.setter
    def pk(self, value):
        setattr(self.values, self.__pkname__, value)
