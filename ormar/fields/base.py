from typing import Any, List, Optional, TYPE_CHECKING, Type, Union

import sqlalchemy
from pydantic import Field, typing
from pydantic.fields import FieldInfo

from ormar import ModelDefinitionError  # noqa I101

if TYPE_CHECKING:  # pragma no cover
    from ormar.models import Model
    from ormar.models import NewBaseModel


class BaseField:
    __type__ = None

    column_type: sqlalchemy.Column
    constraints: List = []
    name: str

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
    def default_value(cls) -> Optional[FieldInfo]:
        if cls.is_auto_primary_key():
            return Field(default=None)
        if cls.has_default():
            default = cls.default if cls.default is not None else cls.server_default
            if callable(default):
                return Field(default_factory=default)
            return Field(default=default)
        return None

    @classmethod
    def get_default(cls) -> Any:
        if cls.has_default():
            default = cls.default if cls.default is not None else cls.server_default
            if callable(default):
                default = default()
            return default

    @classmethod
    def has_default(cls) -> bool:
        return cls.default is not None or cls.server_default is not None

    @classmethod
    def is_auto_primary_key(cls) -> bool:
        if cls.primary_key:
            return cls.autoincrement
        return False

    @classmethod
    def get_column(cls, name: str) -> sqlalchemy.Column:
        return sqlalchemy.Column(
            cls.name or name,
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
