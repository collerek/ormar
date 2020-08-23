import datetime
import decimal
import re
from typing import Any, Optional, Type

import pydantic
import sqlalchemy
from pydantic import Json

from ormar import ModelDefinitionError  # noqa I101
from ormar.fields.base import BaseField  # noqa I101


def is_field_nullable(
    nullable: Optional[bool], default: Any, server_default: Any
) -> bool:
    if nullable is None:
        return default is not None or server_default is not None
    return nullable


def String(
    *,
    name: str = None,
    primary_key: bool = False,
    nullable: bool = None,
    index: bool = False,
    unique: bool = False,
    allow_blank: bool = False,
    strip_whitespace: bool = False,
    min_length: int = None,
    max_length: int = None,
    curtail_length: int = None,
    regex: str = None,
    pydantic_only: bool = False,
    default: Any = None,
    server_default: Any = None,
) -> Type[str]:
    if max_length is None or max_length <= 0:
        raise ModelDefinitionError("Parameter max_length is required for field String")

    namespace = dict(
        __type__=str,
        name=name,
        primary_key=primary_key,
        nullable=is_field_nullable(nullable, default, server_default),
        index=index,
        unique=unique,
        allow_blank=allow_blank,
        strip_whitespace=strip_whitespace,
        min_length=min_length,
        max_length=max_length,
        curtail_length=curtail_length,
        regex=regex and re.compile(regex),
        column_type=sqlalchemy.String(length=max_length),
        pydantic_only=pydantic_only,
        default=default,
        server_default=server_default,
        autoincrement=False,
    )

    return type("String", (pydantic.ConstrainedStr, BaseField), namespace)


def Integer(
    *,
    name: str = None,
    primary_key: bool = False,
    autoincrement: bool = None,
    nullable: bool = None,
    index: bool = False,
    unique: bool = False,
    minimum: int = None,
    maximum: int = None,
    multiple_of: int = None,
    pydantic_only: bool = False,
    default: Any = None,
    server_default: Any = None,
) -> Type[int]:
    namespace = dict(
        __type__=int,
        name=name,
        primary_key=primary_key,
        nullable=is_field_nullable(nullable, default, server_default),
        index=index,
        unique=unique,
        ge=minimum,
        le=maximum,
        multiple_of=multiple_of,
        column_type=sqlalchemy.Integer(),
        pydantic_only=pydantic_only,
        default=default,
        server_default=server_default,
        autoincrement=autoincrement if autoincrement is not None else primary_key,
    )
    return type("Integer", (pydantic.ConstrainedInt, BaseField), namespace)


def Text(
    *,
    name: str = None,
    primary_key: bool = False,
    nullable: bool = None,
    index: bool = False,
    unique: bool = False,
    allow_blank: bool = False,
    strip_whitespace: bool = False,
    pydantic_only: bool = False,
    default: Any = None,
    server_default: Any = None,
) -> Type[str]:
    namespace = dict(
        __type__=str,
        name=name,
        primary_key=primary_key,
        nullable=is_field_nullable(nullable, default, server_default),
        index=index,
        unique=unique,
        allow_blank=allow_blank,
        strip_whitespace=strip_whitespace,
        column_type=sqlalchemy.Text(),
        pydantic_only=pydantic_only,
        default=default,
        server_default=server_default,
        autoincrement=False,
    )

    return type("Text", (pydantic.ConstrainedStr, BaseField), namespace)


def Float(
    *,
    name: str = None,
    primary_key: bool = False,
    nullable: bool = None,
    index: bool = False,
    unique: bool = False,
    minimum: float = None,
    maximum: float = None,
    multiple_of: int = None,
    pydantic_only: bool = False,
    default: Any = None,
    server_default: Any = None,
) -> Type[int]:
    namespace = dict(
        __type__=float,
        name=name,
        primary_key=primary_key,
        nullable=is_field_nullable(nullable, default, server_default),
        index=index,
        unique=unique,
        ge=minimum,
        le=maximum,
        multiple_of=multiple_of,
        column_type=sqlalchemy.Float(),
        pydantic_only=pydantic_only,
        default=default,
        server_default=server_default,
        autoincrement=False,
    )
    return type("Float", (pydantic.ConstrainedFloat, BaseField), namespace)


def Boolean(
    *,
    name: str = None,
    primary_key: bool = False,
    nullable: bool = None,
    index: bool = False,
    unique: bool = False,
    pydantic_only: bool = False,
    default: Any = None,
    server_default: Any = None,
) -> Type[bool]:
    namespace = dict(
        __type__=bool,
        name=name,
        primary_key=primary_key,
        nullable=is_field_nullable(nullable, default, server_default),
        index=index,
        unique=unique,
        column_type=sqlalchemy.Boolean(),
        pydantic_only=pydantic_only,
        default=default,
        server_default=server_default,
        autoincrement=False,
    )
    return type("Boolean", (int, BaseField), namespace)


def DateTime(
    *,
    name: str = None,
    primary_key: bool = False,
    nullable: bool = None,
    index: bool = False,
    unique: bool = False,
    pydantic_only: bool = False,
    default: Any = None,
    server_default: Any = None,
) -> Type[datetime.datetime]:
    namespace = dict(
        __type__=datetime.datetime,
        name=name,
        primary_key=primary_key,
        nullable=is_field_nullable(nullable, default, server_default),
        index=index,
        unique=unique,
        column_type=sqlalchemy.DateTime(),
        pydantic_only=pydantic_only,
        default=default,
        server_default=server_default,
        autoincrement=False,
    )
    return type("DateTime", (datetime.datetime, BaseField), namespace)


def Date(
    *,
    name: str = None,
    primary_key: bool = False,
    nullable: bool = None,
    index: bool = False,
    unique: bool = False,
    pydantic_only: bool = False,
    default: Any = None,
    server_default: Any = None,
) -> Type[datetime.date]:
    namespace = dict(
        __type__=datetime.date,
        name=name,
        primary_key=primary_key,
        nullable=is_field_nullable(nullable, default, server_default),
        index=index,
        unique=unique,
        column_type=sqlalchemy.Date(),
        pydantic_only=pydantic_only,
        default=default,
        server_default=server_default,
        autoincrement=False,
    )
    return type("Date", (datetime.date, BaseField), namespace)


def Time(
    *,
    name: str = None,
    primary_key: bool = False,
    nullable: bool = None,
    index: bool = False,
    unique: bool = False,
    pydantic_only: bool = False,
    default: Any = None,
    server_default: Any = None,
) -> Type[datetime.time]:
    namespace = dict(
        __type__=datetime.time,
        name=name,
        primary_key=primary_key,
        nullable=is_field_nullable(nullable, default, server_default),
        index=index,
        unique=unique,
        column_type=sqlalchemy.Time(),
        pydantic_only=pydantic_only,
        default=default,
        server_default=server_default,
        autoincrement=False,
    )
    return type("Time", (datetime.time, BaseField), namespace)


def JSON(
    *,
    name: str = None,
    primary_key: bool = False,
    nullable: bool = None,
    index: bool = False,
    unique: bool = False,
    pydantic_only: bool = False,
    default: Any = None,
    server_default: Any = None,
) -> Type[Json]:
    namespace = dict(
        __type__=pydantic.Json,
        name=name,
        primary_key=primary_key,
        nullable=is_field_nullable(nullable, default, server_default),
        index=index,
        unique=unique,
        column_type=sqlalchemy.JSON(),
        pydantic_only=pydantic_only,
        default=default,
        server_default=server_default,
        autoincrement=False,
    )

    return type("JSON", (pydantic.Json, BaseField), namespace)


def BigInteger(
    *,
    name: str = None,
    primary_key: bool = False,
    autoincrement: bool = None,
    nullable: bool = None,
    index: bool = False,
    unique: bool = False,
    minimum: int = None,
    maximum: int = None,
    multiple_of: int = None,
    pydantic_only: bool = False,
    default: Any = None,
    server_default: Any = None,
) -> Type[int]:
    namespace = dict(
        __type__=int,
        name=name,
        primary_key=primary_key,
        nullable=is_field_nullable(nullable, default, server_default),
        index=index,
        unique=unique,
        ge=minimum,
        le=maximum,
        multiple_of=multiple_of,
        column_type=sqlalchemy.BigInteger(),
        pydantic_only=pydantic_only,
        default=default,
        server_default=server_default,
        autoincrement=autoincrement if autoincrement is not None else primary_key,
    )
    return type("BigInteger", (pydantic.ConstrainedInt, BaseField), namespace)


def Decimal(
    *,
    name: str = None,
    primary_key: bool = False,
    nullable: bool = None,
    index: bool = False,
    unique: bool = False,
    minimum: float = None,
    maximum: float = None,
    multiple_of: int = None,
    precision: int = None,
    scale: int = None,
    max_digits: int = None,
    decimal_places: int = None,
    pydantic_only: bool = False,
    default: Any = None,
    server_default: Any = None,
) -> Type[decimal.Decimal]:
    if precision is None or precision < 0 or scale is None or scale < 0:
        raise ModelDefinitionError(
            "Parameters scale and precision are required for field Decimal"
        )

    namespace = dict(
        __type__=decimal.Decimal,
        name=name,
        primary_key=primary_key,
        nullable=is_field_nullable(nullable, default, server_default),
        index=index,
        unique=unique,
        ge=minimum,
        le=maximum,
        multiple_of=multiple_of,
        column_type=sqlalchemy.types.DECIMAL(precision=precision, scale=scale),
        precision=precision,
        scale=scale,
        max_digits=max_digits,
        decimal_places=decimal_places,
        pydantic_only=pydantic_only,
        default=default,
        server_default=server_default,
        autoincrement=False,
    )
    return type("Decimal", (pydantic.ConstrainedDecimal, BaseField), namespace)
