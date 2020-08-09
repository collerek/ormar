import datetime
import decimal
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Type, Union

import orm
from orm.exceptions import ModelDefinitionError, RelationshipInstanceError

from pydantic import BaseModel, Json
from pydantic.fields import ModelField

import sqlalchemy

if TYPE_CHECKING:  # pragma no cover
    from orm.models import Model


class BaseField:
    __type__ = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        name = kwargs.pop("name", None)
        args = list(args)
        if args:
            if isinstance(args[0], str):
                if name is not None:
                    raise ModelDefinitionError(
                        "Column name cannot be passed positionally and as a keyword."
                    )
                name = args.pop(0)

        self.name = name
        self._populate_from_kwargs(kwargs)

    def _populate_from_kwargs(self, kwargs: Dict) -> None:
        self.primary_key = kwargs.pop("primary_key", False)
        self.autoincrement = kwargs.pop(
            "autoincrement", self.primary_key and self.__type__ == int
        )

        self.nullable = kwargs.pop("nullable", not self.primary_key)
        self.default = kwargs.pop("default", None)
        self.server_default = kwargs.pop("server_default", None)

        self.index = kwargs.pop("index", None)
        self.unique = kwargs.pop("unique", None)

        self.pydantic_only = kwargs.pop("pydantic_only", False)
        if self.pydantic_only and self.primary_key:
            raise ModelDefinitionError("Primary key column cannot be pydantic only.")

    @property
    def is_required(self) -> bool:
        return (
            not self.nullable and not self.has_default and not self.is_auto_primary_key
        )

    @property
    def default_value(self) -> Any:
        default = self.default if self.default is not None else self.server_default
        return default() if callable(default) else default

    @property
    def has_default(self) -> bool:
        return self.default is not None or self.server_default is not None

    @property
    def is_auto_primary_key(self) -> bool:
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
            server_default=self.server_default,
        )

    def get_column_type(self) -> sqlalchemy.types.TypeEngine:
        raise NotImplementedError()  # pragma: no cover

    def get_constraints(self) -> Optional[List]:
        return []

    def expand_relationship(self, value: Any, child: "Model") -> Any:
        return value


class String(BaseField):
    __type__ = str

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if "length" not in kwargs:
            raise ModelDefinitionError(
                "Param length is required for String model field."
            )
        self.length = kwargs.pop("length")
        super().__init__(*args, **kwargs)

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


class Decimal(BaseField):
    __type__ = decimal.Decimal

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if "length" not in kwargs or "precision" not in kwargs:
            raise ModelDefinitionError(
                "Params length and precision are required for Decimal model field."
            )
        self.length = kwargs.pop("length")
        self.precision = kwargs.pop("precision")
        super().__init__(*args, **kwargs)

    def get_column_type(self) -> sqlalchemy.Column:
        return sqlalchemy.DECIMAL(self.length, self.precision)


def create_dummy_instance(fk: Type["Model"], pk: int = None) -> "Model":
    init_dict = {fk.__pkname__: pk or -1}
    init_dict = {
        **init_dict,
        **{
            k: create_dummy_instance(v.to)
            for k, v in fk.__model_fields__.items()
            if isinstance(v, ForeignKey) and not v.nullable and not v.virtual
        },
    }
    return fk(**init_dict)


class ForeignKey(BaseField):
    def __init__(
        self,
        to: Type["Model"],
        name: str = None,
        related_name: str = None,
        nullable: bool = True,
        virtual: bool = False,
    ) -> None:
        super().__init__(nullable=nullable, name=name)
        self.virtual = virtual
        self.related_name = related_name
        self.to = to

    @property
    def __type__(self) -> Type[BaseModel]:
        return self.to.__pydantic_model__

    def get_constraints(self) -> List[sqlalchemy.schema.ForeignKey]:
        fk_string = self.to.__tablename__ + "." + self.to.__pkname__
        return [sqlalchemy.schema.ForeignKey(fk_string)]

    def get_column_type(self) -> sqlalchemy.Column:
        to_column = self.to.__model_fields__[self.to.__pkname__]
        return to_column.get_column_type()

    def expand_relationship(
        self, value: Any, child: "Model"
    ) -> Union["Model", List["Model"]]:

        if isinstance(value, orm.models.Model) and not isinstance(value, self.to):
            raise RelationshipInstanceError(
                f"Relationship error - expecting: {self.to.__name__}, "
                f"but {value.__class__.__name__} encountered."
            )

        if isinstance(value, list) and not isinstance(value, self.to):
            model = [self.expand_relationship(val, child) for val in value]
            return model

        if isinstance(value, self.to):
            model = value
        elif isinstance(value, dict):
            model = self.to(**value)
        else:
            if not isinstance(value, self.to.pk_type()):
                raise RelationshipInstanceError(
                    f"Relationship error - ForeignKey {self.to.__name__} "
                    f"is of type {self.to.pk_type()} "
                    f"of type {self.__type__} "
                    f"while {type(value)} passed as a parameter."
                )
            model = create_dummy_instance(fk=self.to, pk=value)

        self.add_to_relationship_registry(model, child)

        return model

    def add_to_relationship_registry(self, model: "Model", child: "Model") -> None:
        child_model_name = self.related_name or child.get_name() + "s"
        model._orm_relationship_manager.add_relation(
            model.__class__.__name__.lower(),
            child.__class__.__name__.lower(),
            model,
            child,
            virtual=self.virtual,
        )

        if (
            child_model_name not in model.__fields__
            and child.get_name() not in model.__fields__
        ):
            self.register_reverse_model_fields(model, child, child_model_name)

    @staticmethod
    def register_reverse_model_fields(
        model: "Model", child: "Model", child_model_name: str
    ) -> None:
        model.__fields__[child_model_name] = ModelField(
            name=child_model_name,
            type_=Optional[child.__pydantic_model__],
            model_config=child.__pydantic_model__.__config__,
            class_validators=child.__pydantic_model__.__validators__,
        )
        model.__model_fields__[child_model_name] = ForeignKey(
            child.__class__, name=child_model_name, virtual=True
        )
