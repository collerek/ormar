from __future__ import annotations

import json
from typing import Any
from typing import Set, Dict

import pydantic
import sqlalchemy
from pydantic import BaseConfig, create_model

from orm.exceptions import ModelDefinitionError
from orm.fields import BaseField


def parse_pydantic_field_from_model_fields(object_dict: dict):
    pydantic_fields = {field_name: (
        base_field.__type__,
        ... if (not base_field.nullable and not base_field.default and not base_field.primary_key) else (
            base_field.default() if callable(base_field.default) else base_field.default)
    )
        for field_name, base_field in object_dict.items()
        if isinstance(base_field, BaseField)}
    return pydantic_fields


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
        model_fields = {}
        for field_name, field in attrs.items():
            if isinstance(field, BaseField):
                model_fields[field_name] = field
                if not field.pydantic_only:
                    if field.primary_key:
                        pkname = field_name
                    columns.append(field.get_column(field_name))

        # sqlalchemy table creation
        attrs['__table__'] = sqlalchemy.Table(tablename, metadata, *columns)
        attrs['__columns__'] = columns
        attrs['__pkname__'] = pkname

        if not pkname:
            raise ModelDefinitionError(
                'Table has to have a primary key.'
            )

        # pydantic model creation
        pydantic_fields = parse_pydantic_field_from_model_fields(attrs)
        config = type('Config', (BaseConfig,), {'orm_mode': True})
        pydantic_model = create_model(name, __config__=config, **pydantic_fields)
        attrs['__pydantic_fields__'] = pydantic_fields
        attrs['__pydantic_model__'] = pydantic_model
        attrs['__fields__'] = pydantic_model.__fields__
        attrs['__signature__'] = pydantic_model.__signature__
        attrs['__annotations__'] = pydantic_model.__annotations__

        attrs['__model_fields__'] = model_fields

        new_model = super().__new__(  # type: ignore
            mcs, name, bases, attrs
        )

        return new_model


class Model(metaclass=ModelMetaclass):
    __abstract__ = True

    def __init__(self, *args, **kwargs) -> None:
        if "pk" in kwargs:
            kwargs[self.__pkname__] = kwargs.pop("pk")
        self.values = self.__pydantic_model__(**kwargs)

    def __setattr__(self, key: str, value: Any) -> None:
        if key in self.__fields__:
            if self.is_conversion_to_json_needed(key) and not isinstance(value, str):
                try:
                    value = json.dumps(value)
                except TypeError:  # pragma no cover
                    pass
            setattr(self.values, key, value)
        else:
            super().__setattr__(key, value)

    def __getattribute__(self, key: str) -> Any:
        if key != '__fields__' and key in self.__fields__:
            item = getattr(self.values, key)
            if self.is_conversion_to_json_needed(key) and isinstance(item, str):
                try:
                    item = json.loads(item)
                except TypeError:  # pragma no cover
                    pass
            return item

        return super().__getattribute__(key)

    def is_conversion_to_json_needed(self, column_name: str) -> bool:
        return self.__model_fields__.get(column_name).__type__ == pydantic.Json

    @property
    def pk(self):
        return getattr(self.values, self.__pkname__)

    @pk.setter
    def pk(self, value):
        setattr(self.values, self.__pkname__, value)

    @property
    def pk_column(self) -> sqlalchemy.Column:
        return self.__table__.primary_key.columns.values()[0]

    def dict(self) -> Dict:
        return self.values.dict()

    def from_dict(self, value_dict: Dict) -> None:
        for key, value in value_dict.items():
            setattr(self, key, value)

    def extract_own_model_fields(self) -> Dict:
        related_names = self.extract_related_names()
        self_fields = {k: v for k, v in self.dict().items() if k not in related_names}
        return self_fields

    @classmethod
    def extract_related_names(cls) -> Set:
        related_names = set()
        # for name, field in cls.__fields__.items():
        #     if inspect.isclass(field.type_) and issubclass(field.type_, pydantic.BaseModel):
        #         related_names.add(name)
        #     elif field.sub_fields and any(
        #             [inspect.isclass(f.type_) and issubclass(f.type_, pydantic.BaseModel) for f in field.sub_fields]):
        #         related_names.add(name)
        return related_names

    def extract_model_db_fields(self) -> Dict:
        self_fields = self.extract_own_model_fields()
        self_fields = {k: v for k, v in self_fields.items() if k in self.__table__.columns}
        return self_fields

    async def save(self) -> int:
        self_fields = self.extract_model_db_fields()
        if self.__model_fields__.get(self.__pkname__).autoincrement:
            self_fields.pop(self.__pkname__, None)
        expr = self.__table__.insert()
        expr = expr.values(**self_fields)
        item_id = await self.__database__.execute(expr)
        setattr(self, 'pk', item_id)
        return item_id

    async def update(self, **kwargs: Any) -> int:
        if kwargs:
            new_values = {**self.dict(), **kwargs}
            self.from_dict(new_values)

        self_fields = self.extract_model_db_fields()
        self_fields.pop(self.__pkname__)
        expr = self.__table__.update().values(**self_fields).where(
            self.pk_column == getattr(self, self.__pkname__))
        result = await self.__database__.execute(expr)
        return result

    async def delete(self) -> int:
        expr = self.__table__.delete()
        expr = expr.where(self.pk_column == (getattr(self, self.__pkname__)))
        result = await self.__database__.execute(expr)
        return result

    async def load(self) -> Model:
        expr = self.__table__.select().where(self.pk_column == self.pk)
        row = await self.__database__.fetch_one(expr)
        self.from_dict(dict(row))
        return self
