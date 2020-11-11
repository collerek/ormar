from typing import Any, List, Optional, TYPE_CHECKING, Type, Union

import pydantic
import sqlalchemy
from pydantic import Field, typing
from pydantic.fields import FieldInfo

from ormar import ModelDefinitionError  # noqa I101

if TYPE_CHECKING:  # pragma no cover
    from ormar.models import Model
    from ormar.models import NewBaseModel


class BaseField(FieldInfo):
    __type__ = None

    column_type: sqlalchemy.Column
    constraints: List = []
    name: str
    alias: str

    primary_key: bool
    autoincrement: bool
    nullable: bool
    index: bool
    unique: bool
    pydantic_only: bool
    virtual: bool = False
    choices: typing.Sequence
    to: Type["Model"]
    through: Type["Model"]

    default: Any
    server_default: Any

    @classmethod
    def get_alias(cls) -> str:
        return cls.alias if cls.alias else cls.name

    @classmethod
    def is_valid_field_info_field(cls, field_name: str) -> bool:
        return (
            field_name not in ["default", "default_factory", "alias"]
            and not field_name.startswith("__")
            and hasattr(cls, field_name)
        )

    @classmethod
    def convert_to_pydantic_field_info(cls, allow_null: bool = False) -> FieldInfo:
        base = cls.default_value()
        if base is None:
            base = (
                FieldInfo(default=None)
                if (cls.nullable or allow_null)
                else FieldInfo(default=pydantic.fields.Undefined)
            )
        for attr_name in FieldInfo.__dict__.keys():
            if cls.is_valid_field_info_field(attr_name):
                setattr(base, attr_name, cls.__dict__.get(attr_name))
        return base

    @classmethod
    def default_value(cls, use_server: bool = False) -> Optional[FieldInfo]:
        if cls.is_auto_primary_key():
            return Field(default=None)
        if cls.has_default(use_server=use_server):
            default = cls.default if cls.default is not None else cls.server_default
            if callable(default):
                return Field(default_factory=default)
            return Field(default=default)
        return None

    @classmethod
    def get_default(cls, use_server: bool = False) -> Any:  # noqa CCR001
        if cls.has_default():
            default = (
                cls.default
                if cls.default is not None
                else (cls.server_default if use_server else None)
            )
            if callable(default):
                default = default()
            return default

    @classmethod
    def has_default(cls, use_server: bool = True) -> bool:
        return cls.default is not None or (
            cls.server_default is not None and use_server
        )

    @classmethod
    def is_auto_primary_key(cls) -> bool:
        if cls.primary_key:
            return cls.autoincrement
        return False

    @classmethod
    def get_column(cls, name: str) -> sqlalchemy.Column:
        return sqlalchemy.Column(
            cls.alias or name,
            cls.column_type,
            *cls.constraints,
            primary_key=cls.primary_key,
            nullable=cls.nullable and not cls.primary_key,
            index=cls.index,
            unique=cls.unique,
            default=cls.default,
            server_default=cls.server_default,
        )

    @classmethod
    def expand_relationship(
        cls, value: Any, child: Union["Model", "NewBaseModel"], to_register: bool = True
    ) -> Any:
        return value
