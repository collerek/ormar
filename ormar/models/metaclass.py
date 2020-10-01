import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple, Type, Union

import databases
import pydantic
import sqlalchemy
from pydantic import BaseConfig
from pydantic.fields import FieldInfo, ModelField
from sqlalchemy.sql.schema import ColumnCollectionConstraint

import ormar  # noqa I100
from ormar import ForeignKey, ModelDefinitionError, Integer  # noqa I100
from ormar.fields import BaseField
from ormar.fields.foreign_key import ForeignKeyField
from ormar.fields.many_to_many import ManyToMany, ManyToManyField
from ormar.queryset import QuerySet
from ormar.relations.alias_manager import AliasManager

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model

alias_manager = AliasManager()


class ModelMeta:
    tablename: str
    table: sqlalchemy.Table
    metadata: sqlalchemy.MetaData
    database: databases.Database
    columns: List[sqlalchemy.Column]
    constraints: List[ColumnCollectionConstraint]
    pkname: str
    model_fields: Dict[
        str, Union[Type[BaseField], Type[ForeignKeyField], Type[ManyToManyField]]
    ]
    alias_manager: AliasManager


def register_relation_on_build(table_name: str, field: Type[ForeignKeyField]) -> None:
    alias_manager.add_relation_type(field.to.Meta.tablename, table_name)


def register_many_to_many_relation_on_build(
    table_name: str, field: Type[ManyToManyField]
) -> None:
    alias_manager.add_relation_type(field.through.Meta.tablename, table_name)
    alias_manager.add_relation_type(
        field.through.Meta.tablename, field.to.Meta.tablename
    )


def reverse_field_not_already_registered(
    child: Type["Model"], child_model_name: str, parent_model: Type["Model"]
) -> bool:
    return (
        child_model_name not in parent_model.__fields__
        and child.get_name() not in parent_model.__fields__
    )


def expand_reverse_relationships(model: Type["Model"]) -> None:
    for model_field in model.Meta.model_fields.values():
        if issubclass(model_field, ForeignKeyField):
            child_model_name = model_field.related_name or model.get_name() + "s"
            parent_model = model_field.to
            child = model
            if reverse_field_not_already_registered(
                child, child_model_name, parent_model
            ):
                register_reverse_model_fields(
                    parent_model, child, child_model_name, model_field
                )


def register_reverse_model_fields(
    model: Type["Model"],
    child: Type["Model"],
    child_model_name: str,
    model_field: Type["ForeignKeyField"],
) -> None:
    if issubclass(model_field, ManyToManyField):
        model.Meta.model_fields[child_model_name] = ManyToMany(
            child, through=model_field.through, name=child_model_name, virtual=True
        )
        # register foreign keys on through model
        adjust_through_many_to_many_model(model, child, model_field)
    else:
        model.Meta.model_fields[child_model_name] = ForeignKey(
            child, name=child_model_name, virtual=True
        )


def adjust_through_many_to_many_model(
    model: Type["Model"], child: Type["Model"], model_field: Type[ManyToManyField]
) -> None:
    model_field.through.Meta.model_fields[model.get_name()] = ForeignKey(
        model, name=model.get_name(), ondelete="CASCADE"
    )
    model_field.through.Meta.model_fields[child.get_name()] = ForeignKey(
        child, name=child.get_name(), ondelete="CASCADE"
    )

    create_and_append_m2m_fk(model, model_field)
    create_and_append_m2m_fk(child, model_field)

    create_pydantic_field(model.get_name(), model, model_field)
    create_pydantic_field(child.get_name(), child, model_field)


def create_pydantic_field(
    field_name: str, model: Type["Model"], model_field: Type[ManyToManyField]
) -> None:
    model_field.through.__fields__[field_name] = ModelField(
        name=field_name,
        type_=model,
        model_config=model.__config__,
        required=False,
        class_validators={},
    )


def create_and_append_m2m_fk(
    model: Type["Model"], model_field: Type[ManyToManyField]
) -> None:
    column = sqlalchemy.Column(
        model.get_name(),
        model.Meta.table.columns.get(model.Meta.pkname).type,
        sqlalchemy.schema.ForeignKey(
            model.Meta.tablename + "." + model.Meta.pkname,
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
    )
    model_field.through.Meta.columns.append(column)
    model_field.through.Meta.table.append_column(column)


def check_pk_column_validity(
    field_name: str, field: BaseField, pkname: Optional[str]
) -> Optional[str]:
    if pkname is not None:
        raise ModelDefinitionError("Only one primary key column is allowed.")
    if field.pydantic_only:
        raise ModelDefinitionError("Primary key column cannot be pydantic only")
    return field_name


def sqlalchemy_columns_from_model_fields(
    model_fields: Dict, table_name: str
) -> Tuple[Optional[str], List[sqlalchemy.Column]]:
    columns = []
    pkname = None
    if len(model_fields.keys()) == 0:
        model_fields["id"] = Integer(name="id", primary_key=True)
        logging.warning(
            "Table {table_name} had no fields so auto "
            "Integer primary key named `id` created."
        )
    for field_name, field in model_fields.items():
        if field.primary_key:
            pkname = check_pk_column_validity(field_name, field, pkname)
        if (
            not field.pydantic_only
            and not field.virtual
            and not issubclass(field, ManyToManyField)
        ):
            columns.append(field.get_column(field_name))
        register_relation_in_alias_manager(table_name, field)
    return pkname, columns


def register_relation_in_alias_manager(
    table_name: str, field: Type[ForeignKeyField]
) -> None:
    if issubclass(field, ManyToManyField):
        register_many_to_many_relation_on_build(table_name, field)
    elif issubclass(field, ForeignKeyField):
        register_relation_on_build(table_name, field)


def populate_default_pydantic_field_value(
    type_: Type[BaseField], field: str, attrs: dict
) -> dict:
    def_value = type_.default_value()
    curr_def_value = attrs.get(field, "NONE")
    if curr_def_value == "NONE" and isinstance(def_value, FieldInfo):
        attrs[field] = def_value
    elif curr_def_value == "NONE" and type_.nullable:
        attrs[field] = FieldInfo(default=None)
    return attrs


def populate_pydantic_default_values(attrs: Dict) -> Dict:
    for field, type_ in attrs["__annotations__"].items():
        if issubclass(type_, BaseField):
            if type_.name is None:
                type_.name = field
            attrs = populate_default_pydantic_field_value(type_, field, attrs)
    return attrs


def extract_annotations_and_default_vals(attrs: dict, bases: Tuple) -> dict:
    attrs["__annotations__"] = attrs.get("__annotations__") or bases[0].__dict__.get(
        "__annotations__", {}
    )
    attrs = populate_pydantic_default_values(attrs)
    return attrs


def populate_meta_orm_model_fields(
    attrs: dict, new_model: Type["Model"]
) -> Type["Model"]:
    model_fields = {
        field_name: field
        for field_name, field in attrs["__annotations__"].items()
        if issubclass(field, BaseField)
    }
    new_model.Meta.model_fields = model_fields
    return new_model


def populate_meta_tablename_columns_and_pk(
    name: str, new_model: Type["Model"]
) -> Type["Model"]:
    tablename = name.lower() + "s"
    new_model.Meta.tablename = new_model.Meta.tablename or tablename
    pkname: Optional[str]

    if hasattr(new_model.Meta, "columns"):
        columns = new_model.Meta.table.columns
        pkname = new_model.Meta.pkname
    else:
        pkname, columns = sqlalchemy_columns_from_model_fields(
            new_model.Meta.model_fields, new_model.Meta.tablename
        )

    if pkname is None:
        raise ModelDefinitionError("Table has to have a primary key.")

    new_model.Meta.columns = columns
    new_model.Meta.pkname = pkname

    return new_model


def populate_meta_sqlalchemy_table_if_required(
    new_model: Type["Model"],
) -> Type["Model"]:
    if not hasattr(new_model.Meta, "table"):
        new_model.Meta.table = sqlalchemy.Table(
            new_model.Meta.tablename,
            new_model.Meta.metadata,
            *new_model.Meta.columns,
            *new_model.Meta.constraints,
        )
    return new_model


def get_pydantic_base_orm_config() -> Type[BaseConfig]:
    class Config(BaseConfig):
        orm_mode = True
        arbitrary_types_allowed = True

    return Config


def check_if_field_has_choices(field: Type[BaseField]) -> bool:
    return hasattr(field, "choices") and bool(field.choices)


def model_initialized_and_has_model_fields(model: Type["Model"]) -> bool:
    return hasattr(model, "Meta") and hasattr(model.Meta, "model_fields")


def choices_validator(cls: Type["Model"], values: Dict[str, Any]) -> Dict[str, Any]:
    for field_name, field in cls.Meta.model_fields.items():
        if check_if_field_has_choices(field):
            value = values.get(field_name, ormar.Undefined)
            if value is not ormar.Undefined and value not in field.choices:
                raise ValueError(
                    f"{field_name}: '{values.get(field_name)}' "
                    f"not in allowed choices set:"
                    f" {field.choices}"
                )
    return values


def populate_choices_validators(  # noqa CCR001
    model: Type["Model"], attrs: Dict
) -> None:
    if model_initialized_and_has_model_fields(model):
        for _, field in model.Meta.model_fields.items():
            if check_if_field_has_choices(field):
                validators = attrs.get("__pre_root_validators__", [])
                if choices_validator not in validators:
                    validators.append(choices_validator)
                    attrs["__pre_root_validators__"] = validators


class ModelMetaclass(pydantic.main.ModelMetaclass):
    def __new__(  # type: ignore
        mcs: "ModelMetaclass", name: str, bases: Any, attrs: dict
    ) -> "ModelMetaclass":
        attrs["Config"] = get_pydantic_base_orm_config()
        attrs["__name__"] = name
        attrs = extract_annotations_and_default_vals(attrs, bases)
        new_model = super().__new__(  # type: ignore
            mcs, name, bases, attrs
        )

        if hasattr(new_model, "Meta"):
            if not hasattr(new_model.Meta, "constraints"):
                new_model.Meta.constraints = []
            new_model = populate_meta_orm_model_fields(attrs, new_model)
            new_model = populate_meta_tablename_columns_and_pk(name, new_model)
            new_model = populate_meta_sqlalchemy_table_if_required(new_model)
            expand_reverse_relationships(new_model)
            populate_choices_validators(new_model, attrs)

            if new_model.Meta.pkname not in attrs["__annotations__"]:
                field_name = new_model.Meta.pkname
                field = Integer(name=field_name, primary_key=True)
                attrs["__annotations__"][field_name] = field
                populate_default_pydantic_field_value(
                    field, field_name, attrs  # type: ignore
                )

            new_model = super().__new__(  # type: ignore
                mcs, name, bases, attrs
            )

            new_model.Meta.alias_manager = alias_manager
            new_model.objects = QuerySet(new_model)

        return new_model
