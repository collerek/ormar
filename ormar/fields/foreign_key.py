from typing import Any, Callable, List, Optional, TYPE_CHECKING, Type, Union

import sqlalchemy

import ormar  # noqa I101
from ormar.exceptions import RelationshipInstanceError
from ormar.fields.base import BaseField

if TYPE_CHECKING:  # pragma no cover
    from ormar.models import Model


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


def ForeignKey(
    to: "Model",
    *,
    name: str = None,
    unique: bool = False,
    nullable: bool = True,
    related_name: str = None,
    virtual: bool = False,
) -> Type[object]:
    fk_string = to.Meta.tablename + "." + to.Meta.pkname
    to_field = to.__fields__[to.Meta.pkname]
    namespace = dict(
        to=to,
        name=name,
        nullable=nullable,
        constraints=[sqlalchemy.schema.ForeignKey(fk_string)],
        unique=unique,
        column_type=to_field.type_.column_type,
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
    related_name: str
    virtual: bool

    @classmethod
    def __get_validators__(cls) -> Callable:
        yield cls.validate

    @classmethod
    def validate(cls, value: Any) -> Any:
        return value

    # @property
    # def __type__(self) -> Type[BaseModel]:
    #     return self.to.__pydantic_model__

    # @classmethod
    # def get_column_type(cls) -> sqlalchemy.Column:
    #     to_column = cls.to.Meta.model_fields[cls.to.Meta.pkname]
    #     return to_column.column_type

    @classmethod
    def _extract_model_from_sequence(
        cls, value: List, child: "Model"
    ) -> Union["Model", List["Model"]]:
        return [cls.expand_relationship(val, child) for val in value]

    @classmethod
    def _register_existing_model(cls, value: "Model", child: "Model") -> "Model":
        cls.register_relation(value, child)
        return value

    @classmethod
    def _construct_model_from_dict(cls, value: dict, child: "Model") -> "Model":
        model = cls.to(**value)
        cls.register_relation(model, child)
        return model

    @classmethod
    def _construct_model_from_pk(cls, value: Any, child: "Model") -> "Model":
        if not isinstance(value, cls.to.pk_type()):
            raise RelationshipInstanceError(
                f"Relationship error - ForeignKey {cls.to.__name__} "
                f"is of type {cls.to.pk_type()} "
                f"while {type(value)} passed as a parameter."
            )
        model = create_dummy_instance(fk=cls.to, pk=value)
        cls.register_relation(model, child)
        return model

    @classmethod
    def register_relation(cls, model: "Model", child: "Model") -> None:
        child_model_name = cls.related_name or child.get_name()
        model.Meta._orm_relationship_manager.add_relation(
            model, child, child_model_name, virtual=cls.virtual
        )

    @classmethod
    def expand_relationship(
        cls, value: Any, child: "Model"
    ) -> Optional[Union["Model", List["Model"]]]:
        if value is None:
            return None

        constructors = {
            f"{cls.to.__name__}": cls._register_existing_model,
            "dict": cls._construct_model_from_dict,
            "list": cls._extract_model_from_sequence,
        }

        model = constructors.get(
            value.__class__.__name__, cls._construct_model_from_pk
        )(value, child)
        return model
