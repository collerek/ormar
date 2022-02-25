import datetime
import decimal
import uuid
from enum import Enum
from typing import Any, Optional, Set, TYPE_CHECKING, Type, Union, overload

import pydantic
import sqlalchemy

import ormar  # noqa I101
from ormar import ModelDefinitionError  # noqa I101
from ormar.fields import sqlalchemy_uuid
from ormar.fields.base import BaseField  # noqa I101
from ormar.fields.sqlalchemy_encrypted import EncryptBackends

try:
    from typing import Literal  # type: ignore
except ImportError:  # pragma: no cover
    from typing_extensions import Literal  # type: ignore


def is_field_nullable(
    nullable: Optional[bool],
    default: Any,
    server_default: Any,
    pydantic_only: Optional[bool],
) -> bool:
    """
    Checks if the given field should be nullable/ optional based on parameters given.

    :param nullable: flag explicit setting a column as nullable
    :type nullable: Optional[bool]
    :param default: value or function to be called as default in python
    :type default: Any
    :param server_default: function to be called as default by sql server
    :type server_default: Any
    :param pydantic_only: flag if fields should not be included in the sql table
    :type pydantic_only: Optional[bool]
    :return: result of the check
    :rtype: bool
    """
    if nullable is None:
        return (
            default is not None
            or server_default is not None
            or (pydantic_only is not None and pydantic_only)
        )
    return nullable


def is_auto_primary_key(primary_key: bool, autoincrement: bool) -> bool:
    """
    Checks if field is an autoincrement pk -> if yes it's optional.

    :param primary_key: flag if field is a pk field
    :type primary_key: bool
    :param autoincrement: flag if field should be autoincrement
    :type autoincrement: bool
    :return: result of the check
    :rtype: bool
    """
    return primary_key and autoincrement


def convert_choices_if_needed(
    field_type: "Type",
    choices: Set,
    nullable: bool,
    scale: int = None,
    represent_as_str: bool = False,
) -> Set:
    """
    Converts dates to isoformat as fastapi can check this condition in routes
    and the fields are not yet parsed.
    Converts enums to list of it's values.
    Converts uuids to strings.
    Converts decimal to float with given scale.

    :param field_type: type o the field
    :type field_type: Type
    :param choices: set of choices
    :type choices: Set
    :param scale: scale for decimals
    :type scale: int
    :param nullable: flag if field_nullable
    :type nullable: bool
    :param represent_as_str: flag for bytes fields
    :type represent_as_str: bool
    :param scale: scale for decimals
    :type scale: int
    :return: value, choices list
    :rtype: Tuple[Any, Set]
    """
    choices = {o.value if isinstance(o, Enum) else o for o in choices}
    encoder = ormar.ENCODERS_MAP.get(field_type, lambda x: x)
    if field_type == decimal.Decimal:
        precision = scale
        choices = {encoder(o, precision) for o in choices}
    elif field_type == bytes:
        choices = {encoder(o, represent_as_str) for o in choices}
    elif encoder:
        choices = {encoder(o) for o in choices}
    if nullable:
        choices.add(None)
    return choices


class ModelFieldFactory:
    """
    Default field factory that construct Field classes and populated their values.
    """

    _bases: Any = (BaseField,)
    _type: Any = None
    _sample: Any = None

    def __new__(cls, *args: Any, **kwargs: Any) -> BaseField:  # type: ignore
        cls.validate(**kwargs)

        default = kwargs.pop("default", None)
        server_default = kwargs.pop("server_default", None)
        nullable = kwargs.pop("nullable", None)
        sql_nullable = kwargs.pop("sql_nullable", None)
        pydantic_only = kwargs.pop("pydantic_only", False)

        primary_key = kwargs.pop("primary_key", False)
        autoincrement = kwargs.pop("autoincrement", False)

        encrypt_secret = kwargs.pop("encrypt_secret", None)
        encrypt_backend = kwargs.pop("encrypt_backend", EncryptBackends.NONE)
        encrypt_custom_backend = kwargs.pop("encrypt_custom_backend", None)

        overwrite_pydantic_type = kwargs.pop("overwrite_pydantic_type", None)

        nullable = is_field_nullable(
            nullable, default, server_default, pydantic_only
        ) or is_auto_primary_key(primary_key, autoincrement)
        sql_nullable = (
            False
            if primary_key
            else (nullable if sql_nullable is None else sql_nullable)
        )

        choices = set(kwargs.pop("choices", []))
        if choices:
            choices = convert_choices_if_needed(
                field_type=cls._type,
                choices=choices,
                nullable=nullable,
                scale=kwargs.get("scale", None),
                represent_as_str=kwargs.get("represent_as_base64_str", False),
            )

        namespace = dict(
            __type__=cls._type,
            __pydantic_type__=overwrite_pydantic_type
            if overwrite_pydantic_type is not None
            else cls._type,
            __sample__=cls._sample,
            alias=kwargs.pop("name", None),
            name=None,
            primary_key=primary_key,
            default=default,
            server_default=server_default,
            nullable=nullable,
            sql_nullable=sql_nullable,
            index=kwargs.pop("index", False),
            unique=kwargs.pop("unique", False),
            pydantic_only=pydantic_only,
            autoincrement=autoincrement,
            column_type=cls.get_column_type(**kwargs, sql_nullable=sql_nullable),
            choices=choices,
            encrypt_secret=encrypt_secret,
            encrypt_backend=encrypt_backend,
            encrypt_custom_backend=encrypt_custom_backend,
            **kwargs
        )
        Field = type(cls.__name__, cls._bases, {})
        return Field(**namespace)

    @classmethod
    def get_column_type(cls, **kwargs: Any) -> Any:  # pragma no cover
        """
        Return proper type of db column for given field type.
        Accepts required and optional parameters that each column type accepts.

        :param kwargs: key, value pairs of sqlalchemy options
        :type kwargs: Any
        :return: initialized column with proper options
        :rtype: sqlalchemy Column
        """
        return None

    @classmethod
    def validate(cls, **kwargs: Any) -> None:  # pragma no cover
        """
        Used to validate if all required parameters on a given field type are set.
        :param kwargs: all params passed during construction
        :type kwargs: Any
        """


class String(ModelFieldFactory, str):
    """
    String field factory that construct Field classes and populated their values.
    """

    _type = str
    _sample = "string"

    def __new__(  # type: ignore # noqa CFQ002
        cls,
        *,
        max_length: int,
        min_length: int = None,
        regex: str = None,
        **kwargs: Any
    ) -> BaseField:  # type: ignore
        kwargs = {
            **kwargs,
            **{
                k: v
                for k, v in locals().items()
                if k not in ["cls", "__class__", "kwargs"]
            },
        }
        return super().__new__(cls, **kwargs)

    @classmethod
    def get_column_type(cls, **kwargs: Any) -> Any:
        """
        Return proper type of db column for given field type.
        Accepts required and optional parameters that each column type accepts.

        :param kwargs: key, value pairs of sqlalchemy options
        :type kwargs: Any
        :return: initialized column with proper options
        :rtype: sqlalchemy Column
        """
        return sqlalchemy.String(length=kwargs.get("max_length"))

    @classmethod
    def validate(cls, **kwargs: Any) -> None:
        """
        Used to validate if all required parameters on a given field type are set.
        :param kwargs: all params passed during construction
        :type kwargs: Any
        """
        max_length = kwargs.get("max_length", None)
        if max_length <= 0:
            raise ModelDefinitionError(
                "Parameter max_length is required for field String"
            )


class Integer(ModelFieldFactory, int):
    """
    Integer field factory that construct Field classes and populated their values.
    """

    _type = int
    _sample = 0

    def __new__(  # type: ignore
        cls,
        *,
        minimum: int = None,
        maximum: int = None,
        multiple_of: int = None,
        **kwargs: Any
    ) -> BaseField:
        autoincrement = kwargs.pop("autoincrement", None)
        autoincrement = (
            autoincrement
            if autoincrement is not None
            else kwargs.get("primary_key", False)
        )
        kwargs = {
            **kwargs,
            **{
                k: v
                for k, v in locals().items()
                if k not in ["cls", "__class__", "kwargs"]
            },
        }
        kwargs["ge"] = kwargs["minimum"]
        kwargs["le"] = kwargs["maximum"]
        return super().__new__(cls, **kwargs)

    @classmethod
    def get_column_type(cls, **kwargs: Any) -> Any:
        """
        Return proper type of db column for given field type.
        Accepts required and optional parameters that each column type accepts.

        :param kwargs: key, value pairs of sqlalchemy options
        :type kwargs: Any
        :return: initialized column with proper options
        :rtype: sqlalchemy Column
        """
        return sqlalchemy.Integer()


class Text(ModelFieldFactory, str):
    """
    Text field factory that construct Field classes and populated their values.
    """

    _type = str
    _sample = "text"

    def __new__(cls, **kwargs: Any) -> BaseField:  # type: ignore
        kwargs = {
            **kwargs,
            **{
                k: v
                for k, v in locals().items()
                if k not in ["cls", "__class__", "kwargs"]
            },
        }
        return super().__new__(cls, **kwargs)

    @classmethod
    def get_column_type(cls, **kwargs: Any) -> Any:
        """
        Return proper type of db column for given field type.
        Accepts required and optional parameters that each column type accepts.

        :param kwargs: key, value pairs of sqlalchemy options
        :type kwargs: Any
        :return: initialized column with proper options
        :rtype: sqlalchemy Column
        """
        return sqlalchemy.Text()


class Float(ModelFieldFactory, float):
    """
    Float field factory that construct Field classes and populated their values.
    """

    _type = float
    _sample = 0.0

    def __new__(  # type: ignore
        cls,
        *,
        minimum: float = None,
        maximum: float = None,
        multiple_of: int = None,
        **kwargs: Any
    ) -> BaseField:
        kwargs = {
            **kwargs,
            **{
                k: v
                for k, v in locals().items()
                if k not in ["cls", "__class__", "kwargs"]
            },
        }
        kwargs["ge"] = kwargs["minimum"]
        kwargs["le"] = kwargs["maximum"]
        return super().__new__(cls, **kwargs)

    @classmethod
    def get_column_type(cls, **kwargs: Any) -> Any:
        """
        Return proper type of db column for given field type.
        Accepts required and optional parameters that each column type accepts.

        :param kwargs: key, value pairs of sqlalchemy options
        :type kwargs: Any
        :return: initialized column with proper options
        :rtype: sqlalchemy Column
        """
        return sqlalchemy.Float()


if TYPE_CHECKING:  # pragma: nocover

    def Boolean(**kwargs: Any) -> bool:
        pass

else:

    class Boolean(ModelFieldFactory, int):
        """
        Boolean field factory that construct Field classes and populated their values.
        """

        _type = bool
        _sample = True

        @classmethod
        def get_column_type(cls, **kwargs: Any) -> Any:
            """
            Return proper type of db column for given field type.
            Accepts required and optional parameters that each column type accepts.

            :param kwargs: key, value pairs of sqlalchemy options
            :type kwargs: Any
            :return: initialized column with proper options
            :rtype: sqlalchemy Column
            """
            return sqlalchemy.Boolean()


class DateTime(ModelFieldFactory, datetime.datetime):
    """
    DateTime field factory that construct Field classes and populated their values.
    """

    _type = datetime.datetime
    _sample = "datetime"

    def __new__(  # type: ignore # noqa CFQ002
        cls, *, timezone: bool = False, **kwargs: Any
    ) -> BaseField:  # type: ignore
        kwargs = {
            **kwargs,
            **{
                k: v
                for k, v in locals().items()
                if k not in ["cls", "__class__", "kwargs"]
            },
        }
        return super().__new__(cls, **kwargs)

    @classmethod
    def get_column_type(cls, **kwargs: Any) -> Any:
        """
        Return proper type of db column for given field type.
        Accepts required and optional parameters that each column type accepts.

        :param kwargs: key, value pairs of sqlalchemy options
        :type kwargs: Any
        :return: initialized column with proper options
        :rtype: sqlalchemy Column
        """
        return sqlalchemy.DateTime(timezone=kwargs.get("timezone", False))


class Date(ModelFieldFactory, datetime.date):
    """
    Date field factory that construct Field classes and populated their values.
    """

    _type = datetime.date
    _sample = "date"

    @classmethod
    def get_column_type(cls, **kwargs: Any) -> Any:
        """
        Return proper type of db column for given field type.
        Accepts required and optional parameters that each column type accepts.

        :param kwargs: key, value pairs of sqlalchemy options
        :type kwargs: Any
        :return: initialized column with proper options
        :rtype: sqlalchemy Column
        """
        return sqlalchemy.Date()


class Time(ModelFieldFactory, datetime.time):
    """
    Time field factory that construct Field classes and populated their values.
    """

    _type = datetime.time
    _sample = "time"

    def __new__(  # type: ignore # noqa CFQ002
        cls, *, timezone: bool = False, **kwargs: Any
    ) -> BaseField:  # type: ignore
        kwargs = {
            **kwargs,
            **{
                k: v
                for k, v in locals().items()
                if k not in ["cls", "__class__", "kwargs"]
            },
        }
        return super().__new__(cls, **kwargs)

    @classmethod
    def get_column_type(cls, **kwargs: Any) -> Any:
        """
        Return proper type of db column for given field type.
        Accepts required and optional parameters that each column type accepts.

        :param kwargs: key, value pairs of sqlalchemy options
        :type kwargs: Any
        :return: initialized column with proper options
        :rtype: sqlalchemy Column
        """
        return sqlalchemy.Time(timezone=kwargs.get("timezone", False))


class JSON(ModelFieldFactory, pydantic.Json):
    """
    JSON field factory that construct Field classes and populated their values.
    """

    _type = pydantic.Json
    _sample = '{"json": "json"}'

    @classmethod
    def get_column_type(cls, **kwargs: Any) -> Any:
        """
        Return proper type of db column for given field type.
        Accepts required and optional parameters that each column type accepts.

        :param kwargs: key, value pairs of sqlalchemy options
        :type kwargs: Any
        :return: initialized column with proper options
        :rtype: sqlalchemy Column
        """
        return sqlalchemy.JSON(none_as_null=kwargs.get("sql_nullable", False))


if TYPE_CHECKING:  # pragma: nocover # noqa: C901

    @overload
    def LargeBinary(  # type: ignore
        max_length: int, *, represent_as_base64_str: Literal[True], **kwargs: Any
    ) -> str:
        ...

    @overload
    def LargeBinary(  # type: ignore
        max_length: int, *, represent_as_base64_str: Literal[False], **kwargs: Any
    ) -> bytes:
        ...

    @overload
    def LargeBinary(
        max_length: int, represent_as_base64_str: Literal[False] = ..., **kwargs: Any
    ) -> bytes:
        ...

    def LargeBinary(
        max_length: int, represent_as_base64_str: bool = False, **kwargs: Any
    ) -> Union[str, bytes]:
        pass

else:

    class LargeBinary(ModelFieldFactory, bytes):
        """
        LargeBinary field factory that construct Field classes
        and populated their values.
        """

        _type = bytes
        _sample = "bytes"

        def __new__(  # type: ignore # noqa CFQ002
            cls,
            *,
            max_length: int,
            represent_as_base64_str: bool = False,
            **kwargs: Any
        ) -> BaseField:  # type: ignore
            kwargs = {
                **kwargs,
                **{
                    k: v
                    for k, v in locals().items()
                    if k not in ["cls", "__class__", "kwargs"]
                },
            }
            return super().__new__(cls, **kwargs)

        @classmethod
        def get_column_type(cls, **kwargs: Any) -> Any:
            """
            Return proper type of db column for given field type.
            Accepts required and optional parameters that each column type accepts.

            :param kwargs: key, value pairs of sqlalchemy options
            :type kwargs: Any
            :return: initialized column with proper options
            :rtype: sqlalchemy Column
            """
            return sqlalchemy.LargeBinary(length=kwargs.get("max_length"))

        @classmethod
        def validate(cls, **kwargs: Any) -> None:
            """
            Used to validate if all required parameters on a given field type are set.
            :param kwargs: all params passed during construction
            :type kwargs: Any
            """
            max_length = kwargs.get("max_length", None)
            if max_length <= 0:
                raise ModelDefinitionError(
                    "Parameter max_length is required for field LargeBinary"
                )


class BigInteger(Integer, int):
    """
    BigInteger field factory that construct Field classes and populated their values.
    """

    _type = int
    _sample = 0

    def __new__(  # type: ignore
        cls,
        *,
        minimum: int = None,
        maximum: int = None,
        multiple_of: int = None,
        **kwargs: Any
    ) -> BaseField:
        autoincrement = kwargs.pop("autoincrement", None)
        autoincrement = (
            autoincrement
            if autoincrement is not None
            else kwargs.get("primary_key", False)
        )
        kwargs = {
            **kwargs,
            **{
                k: v
                for k, v in locals().items()
                if k not in ["cls", "__class__", "kwargs"]
            },
        }
        kwargs["ge"] = kwargs["minimum"]
        kwargs["le"] = kwargs["maximum"]
        return super().__new__(cls, **kwargs)

    @classmethod
    def get_column_type(cls, **kwargs: Any) -> Any:
        """
        Return proper type of db column for given field type.
        Accepts required and optional parameters that each column type accepts.

        :param kwargs: key, value pairs of sqlalchemy options
        :type kwargs: Any
        :return: initialized column with proper options
        :rtype: sqlalchemy Column
        """
        return sqlalchemy.BigInteger()


class SmallInteger(Integer, int):
    """
    SmallInteger field factory that construct Field classes and populated their values.
    """

    _type = int
    _sample = 0

    def __new__(  # type: ignore
        cls,
        *,
        minimum: int = None,
        maximum: int = None,
        multiple_of: int = None,
        **kwargs: Any
    ) -> BaseField:
        autoincrement = kwargs.pop("autoincrement", None)
        autoincrement = (
            autoincrement
            if autoincrement is not None
            else kwargs.get("primary_key", False)
        )
        kwargs = {
            **kwargs,
            **{
                k: v
                for k, v in locals().items()
                if k not in ["cls", "__class__", "kwargs"]
            },
        }
        kwargs["ge"] = kwargs["minimum"]
        kwargs["le"] = kwargs["maximum"]
        return super().__new__(cls, **kwargs)

    @classmethod
    def get_column_type(cls, **kwargs: Any) -> Any:
        """
        Return proper type of db column for given field type.
        Accepts required and optional parameters that each column type accepts.

        :param kwargs: key, value pairs of sqlalchemy options
        :type kwargs: Any
        :return: initialized column with proper options
        :rtype: sqlalchemy Column
        """
        return sqlalchemy.SmallInteger()


class Decimal(ModelFieldFactory, decimal.Decimal):
    """
    Decimal field factory that construct Field classes and populated their values.
    """

    _type = decimal.Decimal
    _sample = 0.0

    def __new__(  # type: ignore # noqa CFQ002
        cls,
        *,
        minimum: float = None,
        maximum: float = None,
        multiple_of: int = None,
        precision: int = None,
        scale: int = None,
        max_digits: int = None,
        decimal_places: int = None,
        **kwargs: Any
    ) -> BaseField:
        kwargs = {
            **kwargs,
            **{
                k: v
                for k, v in locals().items()
                if k not in ["cls", "__class__", "kwargs"]
            },
        }
        kwargs["ge"] = kwargs["minimum"]
        kwargs["le"] = kwargs["maximum"]

        if kwargs.get("max_digits"):
            kwargs["precision"] = kwargs["max_digits"]
        elif kwargs.get("precision"):
            kwargs["max_digits"] = kwargs["precision"]

        if kwargs.get("decimal_places"):
            kwargs["scale"] = kwargs["decimal_places"]
        elif kwargs.get("scale"):
            kwargs["decimal_places"] = kwargs["scale"]

        return super().__new__(cls, **kwargs)

    @classmethod
    def get_column_type(cls, **kwargs: Any) -> Any:
        """
        Return proper type of db column for given field type.
        Accepts required and optional parameters that each column type accepts.

        :param kwargs: key, value pairs of sqlalchemy options
        :type kwargs: Any
        :return: initialized column with proper options
        :rtype: sqlalchemy Column
        """
        precision = kwargs.get("precision")
        scale = kwargs.get("scale")
        return sqlalchemy.DECIMAL(precision=precision, scale=scale)

    @classmethod
    def validate(cls, **kwargs: Any) -> None:
        """
        Used to validate if all required parameters on a given field type are set.
        :param kwargs: all params passed during construction
        :type kwargs: Any
        """
        precision = kwargs.get("precision")
        scale = kwargs.get("scale")
        if precision is None or precision < 0 or scale is None or scale < 0:
            raise ModelDefinitionError(
                "Parameters scale and precision are required for field Decimal"
            )


class UUID(ModelFieldFactory, uuid.UUID):
    """
    UUID field factory that construct Field classes and populated their values.
    """

    _type = uuid.UUID
    _sample = "uuid"

    def __new__(  # type: ignore # noqa CFQ002
        cls, *, uuid_format: str = "hex", **kwargs: Any
    ) -> BaseField:
        kwargs = {
            **kwargs,
            **{
                k: v
                for k, v in locals().items()
                if k not in ["cls", "__class__", "kwargs"]
            },
        }

        return super().__new__(cls, **kwargs)

    @classmethod
    def get_column_type(cls, **kwargs: Any) -> Any:
        """
        Return proper type of db column for given field type.
        Accepts required and optional parameters that each column type accepts.

        :param kwargs: key, value pairs of sqlalchemy options
        :type kwargs: Any
        :return: initialized column with proper options
        :rtype: sqlalchemy Column
        """
        uuid_format = kwargs.get("uuid_format", "hex")
        return sqlalchemy_uuid.UUID(uuid_format=uuid_format)
