from typing import Any, List, Optional, TYPE_CHECKING, Type, Union

import sqlalchemy
from pydantic import BaseModel, create_model
from sqlalchemy import UniqueConstraint

import ormar  # noqa I101
from ormar.exceptions import RelationshipInstanceError
from ormar.fields.base import BaseField

if TYPE_CHECKING:  # pragma no cover
    from ormar.models import Model, NewBaseModel
    from ormar.fields import ManyToManyField


def create_dummy_instance(fk: Type["Model"], pk: Any = None) -> "Model":
    init_dict = {
        **{fk.Meta.pkname: pk or -1, "__pk_only__": True},
        **{
            k: create_dummy_instance(v.to)
            for k, v in fk.Meta.model_fields.items()
            if isinstance(v, ForeignKeyField) and not v.nullable and not v.virtual
        },
    }
    return fk(**init_dict)


def create_dummy_model(
    base_model: Type["Model"],
    pk_field: Type[Union[BaseField, "ForeignKeyField", "ManyToManyField"]],
) -> Type["BaseModel"]:
    fields = {f"{pk_field.name}": (pk_field.__type__, None)}
    dummy_model = create_model(
        f"PkOnly{base_model.get_name(lower=False)}", **fields  # type: ignore
    )
    return dummy_model


class UniqueColumns(UniqueConstraint):
    pass


def ForeignKey(  # noqa CFQ002
    to: Type["Model"],
    *,
    name: str = None,
    unique: bool = False,
    nullable: bool = True,
    related_name: str = None,
    virtual: bool = False,
    onupdate: str = None,
    ondelete: str = None,
    **kwargs: Any,
) -> Any:
    fk_string = to.Meta.tablename + "." + to.get_column_alias(to.Meta.pkname)
    to_field = to.Meta.model_fields[to.Meta.pkname]
    pk_only_model = create_dummy_model(to, to_field)
    __type__ = (
        Union[to_field.__type__, to, pk_only_model]
        if not nullable
        else Optional[Union[to_field.__type__, to, pk_only_model]]
    )
    namespace = dict(
        __type__=__type__,
        to=to,
        alias=name,
        name=kwargs.pop("real_name", None),
        nullable=nullable,
        constraints=[
            sqlalchemy.schema.ForeignKey(
                fk_string, ondelete=ondelete, onupdate=onupdate
            )
        ],
        unique=unique,
        column_type=to_field.column_type,
        related_name=related_name,
        virtual=virtual,
        primary_key=False,
        index=False,
        pydantic_only=False,
        default=None,
        server_default=None,
    )

    return type("ForeignKey", (ForeignKeyField, BaseField), namespace)


class ForeignKeyField(BaseField):
    to: Type["Model"]
    name: str
    related_name: str
    virtual: bool

    @classmethod
    def _extract_model_from_sequence(
        cls, value: List, child: "Model", to_register: bool
    ) -> List["Model"]:
        return [
            cls.expand_relationship(val, child, to_register)  # type: ignore
            for val in value
        ]

    @classmethod
    def _register_existing_model(
        cls, value: "Model", child: "Model", to_register: bool
    ) -> "Model":
        if to_register:
            cls.register_relation(value, child)
        return value

    @classmethod
    def _construct_model_from_dict(
        cls, value: dict, child: "Model", to_register: bool
    ) -> "Model":
        if len(value.keys()) == 1 and list(value.keys())[0] == cls.to.Meta.pkname:
            value["__pk_only__"] = True
        model = cls.to(**value)
        if to_register:
            cls.register_relation(model, child)
        return model

    @classmethod
    def _construct_model_from_pk(
        cls, value: Any, child: "Model", to_register: bool
    ) -> "Model":
        if not isinstance(value, cls.to.pk_type()):
            raise RelationshipInstanceError(
                f"Relationship error - ForeignKey {cls.to.__name__} "
                f"is of type {cls.to.pk_type()} "
                f"while {type(value)} passed as a parameter."
            )
        model = create_dummy_instance(fk=cls.to, pk=value)
        if to_register:
            cls.register_relation(model, child)
        return model

    @classmethod
    def register_relation(cls, model: "Model", child: "Model") -> None:
        model._orm.add(
            parent=model, child=child, child_name=cls.related_name, virtual=cls.virtual
        )

    @classmethod
    def expand_relationship(
        cls, value: Any, child: Union["Model", "NewBaseModel"], to_register: bool = True
    ) -> Optional[Union["Model", List["Model"]]]:
        if value is None:
            return None if not cls.virtual else []

        constructors = {
            f"{cls.to.__name__}": cls._register_existing_model,
            "dict": cls._construct_model_from_dict,
            "list": cls._extract_model_from_sequence,
        }

        model = constructors.get(  # type: ignore
            value.__class__.__name__, cls._construct_model_from_pk
        )(value, child, to_register)
        return model
