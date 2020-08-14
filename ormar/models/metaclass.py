import copy
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple, Type

import sqlalchemy
from pydantic import BaseConfig, create_model
from pydantic.fields import ModelField

from ormar import ForeignKey, ModelDefinitionError  # noqa I100
from ormar.fields import BaseField
from ormar.relations import RelationshipManager

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model

relationship_manager = RelationshipManager()


def parse_pydantic_field_from_model_fields(object_dict: dict) -> Dict[str, Tuple]:
    pydantic_fields = {
        field_name: (
            base_field.__type__,
            ... if base_field.is_required else base_field.default_value,
        )
        for field_name, base_field in object_dict.items()
        if isinstance(base_field, BaseField)
    }
    return pydantic_fields


def register_relation_on_build(table_name: str, field: ForeignKey, name: str) -> None:
    child_relation_name = (
        field.to.get_name(title=True)
        + "_"
        + (field.related_name or (name.lower() + "s"))
    )
    reverse_name = child_relation_name
    relation_name = name.lower().title() + "_" + field.to.get_name()
    relationship_manager.add_relation_type(
        relation_name, reverse_name, field, table_name
    )


def expand_reverse_relationships(model: Type["Model"]) -> None:
    for model_field in model.__model_fields__.values():
        if isinstance(model_field, ForeignKey):
            child_model_name = model_field.related_name or model.get_name() + "s"
            parent_model = model_field.to
            child = model
            if (
                child_model_name not in parent_model.__fields__
                and child.get_name() not in parent_model.__fields__
            ):
                register_reverse_model_fields(parent_model, child, child_model_name)


def register_reverse_model_fields(
    model: Type["Model"], child: Type["Model"], child_model_name: str
) -> None:
    model.__fields__[child_model_name] = ModelField(
        name=child_model_name,
        type_=Optional[child.__pydantic_model__],
        model_config=child.__pydantic_model__.__config__,
        class_validators=child.__pydantic_model__.__validators__,
    )
    model.__model_fields__[child_model_name] = ForeignKey(
        child, name=child_model_name, virtual=True
    )


def sqlalchemy_columns_from_model_fields(
    name: str, object_dict: Dict, table_name: str
) -> Tuple[Optional[str], List[sqlalchemy.Column], Dict[str, BaseField]]:
    columns = []
    pkname = None
    model_fields = {
        field_name: field
        for field_name, field in object_dict.items()
        if isinstance(field, BaseField)
    }
    for field_name, field in model_fields.items():
        if field.primary_key:
            if pkname is not None:
                raise ModelDefinitionError("Only one primary key column is allowed.")
            pkname = field_name
        if not field.pydantic_only:
            columns.append(field.get_column(field_name))
        if isinstance(field, ForeignKey):
            register_relation_on_build(table_name, field, name)

    return pkname, columns, model_fields


def get_pydantic_base_orm_config() -> Type[BaseConfig]:
    class Config(BaseConfig):
        orm_mode = True

    return Config


class ModelMetaclass(type):
    def __new__(mcs: type, name: str, bases: Any, attrs: dict) -> type:
        new_model = super().__new__(  # type: ignore
            mcs, name, bases, attrs
        )

        if attrs.get("__abstract__"):
            return new_model

        tablename = attrs.get("__tablename__", name.lower() + "s")
        attrs["__tablename__"] = tablename
        metadata = attrs["__metadata__"]

        # sqlalchemy table creation
        pkname, columns, model_fields = sqlalchemy_columns_from_model_fields(
            name, attrs, tablename
        )
        attrs["__table__"] = sqlalchemy.Table(tablename, metadata, *columns)
        attrs["__columns__"] = columns
        attrs["__pkname__"] = pkname

        if not pkname:
            raise ModelDefinitionError("Table has to have a primary key.")

        # pydantic model creation
        pydantic_fields = parse_pydantic_field_from_model_fields(attrs)
        pydantic_model = create_model(
            name, __config__=get_pydantic_base_orm_config(), **pydantic_fields
        )
        attrs["__pydantic_fields__"] = pydantic_fields
        attrs["__pydantic_model__"] = pydantic_model
        attrs["__fields__"] = copy.deepcopy(pydantic_model.__fields__)
        attrs["__signature__"] = copy.deepcopy(pydantic_model.__signature__)
        attrs["__annotations__"] = copy.deepcopy(pydantic_model.__annotations__)

        attrs["__model_fields__"] = model_fields
        attrs["_orm_relationship_manager"] = relationship_manager

        new_model = super().__new__(  # type: ignore
            mcs, name, bases, attrs
        )

        expand_reverse_relationships(new_model)

        return new_model
