from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple, Type, Union

import databases
import pydantic
import sqlalchemy
from pydantic import BaseConfig
from pydantic.fields import FieldInfo

from ormar import ForeignKey, ModelDefinitionError  # noqa I100
from ormar.fields import BaseField
from ormar.fields.foreign_key import ForeignKeyField
from ormar.queryset import QuerySet
from ormar.relations import AliasManager

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model

relationship_manager = AliasManager()


class ModelMeta:
    tablename: str
    table: sqlalchemy.Table
    metadata: sqlalchemy.MetaData
    database: databases.Database
    columns: List[sqlalchemy.Column]
    pkname: str
    model_fields: Dict[str, Union[BaseField, ForeignKey]]
    alias_manager: AliasManager


def register_relation_on_build(table_name: str, field: ForeignKey) -> None:
    relationship_manager.add_relation_type(field, table_name)


def expand_reverse_relationships(model: Type["Model"]) -> None:
    for model_field in model.Meta.model_fields.values():
        if issubclass(model_field, ForeignKeyField):
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
    model.Meta.model_fields[child_model_name] = ForeignKey(
        child, name=child_model_name, virtual=True
    )


def sqlalchemy_columns_from_model_fields(
    model_fields: Dict, table_name: str
) -> Tuple[Optional[str], List[sqlalchemy.Column]]:
    columns = []
    pkname = None
    for field_name, field in model_fields.items():
        if field.primary_key:
            if pkname is not None:
                raise ModelDefinitionError("Only one primary key column is allowed.")
            if field.pydantic_only:
                raise ModelDefinitionError("Primary key column cannot be pydantic only")
            pkname = field_name
        if not field.pydantic_only:
            columns.append(field.get_column(field_name))
        if issubclass(field, ForeignKeyField):
            register_relation_on_build(table_name, field)

    return pkname, columns


def populate_pydantic_default_values(attrs: Dict) -> Dict:
    for field, type_ in attrs["__annotations__"].items():
        if issubclass(type_, BaseField):
            if type_.name is None:
                type_.name = field
            def_value = type_.default_value()
            curr_def_value = attrs.get(field, "NONE")
            if curr_def_value == "NONE" and isinstance(def_value, FieldInfo):
                attrs[field] = def_value
            elif curr_def_value == "NONE" and type_.nullable:
                attrs[field] = FieldInfo(default=None)
    return attrs


def get_pydantic_base_orm_config() -> Type[BaseConfig]:
    class Config(BaseConfig):
        orm_mode = True
        arbitrary_types_allowed = True
        # extra = Extra.allow

    return Config


class ModelMetaclass(pydantic.main.ModelMetaclass):
    def __new__(mcs: type, name: str, bases: Any, attrs: dict) -> type:

        attrs["Config"] = get_pydantic_base_orm_config()
        new_model = super().__new__(  # type: ignore
            mcs, name, bases, attrs
        )

        if hasattr(new_model, "Meta"):

            annotations = attrs.get("__annotations__") or new_model.__annotations__
            attrs["__annotations__"] = annotations
            attrs = populate_pydantic_default_values(attrs)

            attrs["__module__"] = attrs["__module__"] or bases[0].__module__
            attrs["__annotations__"] = (
                attrs["__annotations__"] or bases[0].__annotations__
            )

            tablename = name.lower() + "s"
            new_model.Meta.tablename = new_model.Meta.tablename or tablename

            # sqlalchemy table creation

            model_fields = {
                field_name: field
                for field_name, field in attrs["__annotations__"].items()
                if issubclass(field, BaseField)
            }

            if hasattr(new_model.Meta, "columns"):
                columns = new_model.Meta.table.columns
                pkname = new_model.Meta.pkname
            else:
                pkname, columns = sqlalchemy_columns_from_model_fields(
                    model_fields, new_model.Meta.tablename
                )

            if not hasattr(new_model.Meta, "table"):
                new_model.Meta.table = sqlalchemy.Table(
                    new_model.Meta.tablename, new_model.Meta.metadata, *columns
                )

            new_model.Meta.columns = columns
            new_model.Meta.pkname = pkname

            if not pkname:
                raise ModelDefinitionError("Table has to have a primary key.")

            new_model.Meta.model_fields = model_fields
            expand_reverse_relationships(new_model)

            new_model = super().__new__(  # type: ignore
                mcs, name, bases, attrs
            )

            new_model.Meta.alias_manager = relationship_manager
            new_model.objects = QuerySet(new_model)

        return new_model
