import logging
from typing import Dict, List, Optional, TYPE_CHECKING, Tuple, Type, Union, cast

import sqlalchemy
from pydantic.typing import ForwardRef

import ormar  # noqa: I100, I202
from ormar.models.descriptors import RelationDescriptor
from ormar.models.helpers.pydantic import create_pydantic_field, get_pydantic_field
from ormar.models.helpers.related_names_validation import (
    validate_related_names_in_relations,
)

if TYPE_CHECKING:  # pragma no cover
    from ormar import (
        Model,
        ModelMeta,
        ManyToManyField,
        BaseField,
        ForeignKeyField,
        PrimaryKeyConstraint,
    )
    from ormar.models import NewBaseModel


def adjust_through_many_to_many_model(model_field: "ManyToManyField") -> None:
    """
    Registers m2m relation on through model.
    Sets ormar.ForeignKey from through model to both child and parent models.
    Sets sqlalchemy.ForeignKey to both child and parent models.
    Sets pydantic fields with child and parent model types.

    :param model_field: relation field defined in parent model
    :type model_field: ManyToManyField
    """
    parent_name = model_field.default_target_field_name()
    child_name = model_field.default_source_field_name()

    create_through_relation_fields(
        model_field=model_field, target_model=model_field.to, field_name=parent_name
    )
    create_through_relation_fields(
        model_field=model_field, target_model=model_field.owner, field_name=child_name,
    )


def create_through_relation_fields(
    model_field: "ManyToManyField", target_model: Type["Model"], field_name: str
) -> None:
    model_fields = model_field.through.Meta.model_fields
    names = None
    if model_field.self_reference and model_field.is_compound:
        if field_name == model_field.default_target_field_name():
            prefix = "from_"
        else:
            prefix = "to_"
        names = {
            pk_name: f"{prefix}{target_model.get_name()}_{pk_name}"
            for pk_name in target_model.pk_aliases_list
        }
    model_fields[field_name] = ormar.ForeignKey(  # type: ignore
        target_model,
        real_name=field_name,
        ondelete="CASCADE",
        owner=model_field.through,
        names=names,
    )
    create_and_append_m2m_fk(
        model=target_model, model_field=model_field, field_name=field_name
    )
    create_pydantic_field(field_name, target_model, model_field)
    setattr(model_field.through, field_name, RelationDescriptor(name=field_name))


def create_and_append_m2m_fk(
    model: Type["Model"], model_field: "ManyToManyField", field_name: str
) -> None:
    """
    Registers sqlalchemy Column with sqlalchemy.ForeignKey leading to the model.

    Newly created field is added to m2m relation through model Meta columns and table.

    :param field_name: name of the column to create
    :type field_name: str
    :param model: Model class to which FK should be created
    :type model: Model class
    :param model_field: field with ManyToMany relation
    :type model_field: ManyToManyField field
    """
    pk_columns = model.pk_columns
    target_table = model.Meta.tablename
    if not isinstance(pk_columns, list):
        pk_column = pk_columns
        column = sqlalchemy.Column(
            field_name,
            pk_column.type,
            sqlalchemy.schema.ForeignKey(
                f"{target_table}.{pk_column.name}",
                ondelete="CASCADE",
                onupdate="CASCADE",
                name=f"fk_{model_field.through.Meta.tablename}_{target_table}"
                f"_{field_name}_{pk_column.name}",
            ),
        )
        model_field.through.Meta.columns.append(column)
        model_field.through.Meta.table.append_column(column)
    else:
        relation_columns = []
        for pk_column in pk_columns:
            col_name = f"{field_name}_{pk_column.name}"
            relation_columns.append(col_name)
            column = sqlalchemy.Column(col_name, pk_column.type,)
            model_field.through.Meta.columns.append(column)
            model_field.through.Meta.table.append_column(column)
        fk_constraint = ormar.ForeignKeyConstraint(
            to=model,
            columns=relation_columns,
            related_columns=[f"{pk_column.name}" for pk_column in pk_columns],
            db_name=f"fk_{model_field.through.Meta.tablename}_{target_table}"
            f"_{field_name}_{model.pk_name_str}",
        )
        model_field.through.Meta.table.append_constraint(fk_constraint)


def check_pk_column_validity(
    field_name: str, field: "BaseField", pkname: Optional[str]
) -> Optional[str]:
    """
    Receives the field marked as primary key and verifies if the pkname
    was not already set (only one allowed per model) and if field is not marked
    as pydantic_only as it needs to be a database field.

    :raises ModelDefintionError: if pkname already set or field is pydantic_only
    :param field_name: name of field
    :type field_name: str
    :param field: ormar.Field
    :type field: BaseField
    :param pkname: already set pkname
    :type pkname: Optional[str]
    :return: name of the field that should be set as pkname
    :rtype: str
    """
    if pkname is not None:
        raise ormar.ModelDefinitionError("Only one primary key column is allowed.")
    if field.pydantic_only:
        raise ormar.ModelDefinitionError("Primary key column cannot be pydantic only")
    return field_name


def sqlalchemy_columns_from_model_fields(
    model_fields: Dict, new_model: Type["Model"]
) -> Tuple[Optional[str], List[sqlalchemy.Column]]:
    """
    Iterates over declared on Model model fields and extracts fields that
    should be treated as database fields.

    If the model is empty it sets mandatory id field as primary key
    (used in through models in m2m relations).

    Triggers a validation of relation_names in relation fields. If multiple fields
    are leading to the same related model only one can have empty related_name param.
    Also related_names have to be unique.

    Trigger validation of primary_key - only one and required pk can be set,
    cannot be pydantic_only.

    Append fields to columns if it's not pydantic_only,
    virtual ForeignKey or ManyToMany field.

    Sets `owner` on each model_field as reference to newly created Model.

    :raises ModelDefinitionError: if validation of related_names fail,
    or pkname validation fails.
    :param model_fields: dictionary of declared ormar model fields
    :type model_fields: Dict[str, ormar.Field]
    :param new_model:
    :type new_model: Model class
    :return: pkname, list of sqlalchemy columns
    :rtype: Tuple[Optional[str], List[sqlalchemy.Column]]
    """
    if len(model_fields.keys()) == 0:
        model_fields["id"] = ormar.Integer(name="id", primary_key=True)
        logging.warning(
            f"Table {new_model.Meta.tablename} had no fields so auto "
            "Integer primary key named `id` created."
        )
    validate_related_names_in_relations(model_fields, new_model)
    return _process_fields(model_fields=model_fields, new_model=new_model)


def _process_fields(
    model_fields: Dict, new_model: Type["Model"]
) -> Tuple[Optional[str], List[sqlalchemy.Column]]:
    """
    Helper method.

    Populates pkname and columns.
    Trigger validation of primary_key - only one and required pk can be set,
    cannot be pydantic_only.

    Append fields to columns if it's not pydantic_only,
    virtual ForeignKey or ManyToMany field.

    Sets `owner` on each model_field as reference to newly created Model.

    :raises ModelDefinitionError: if validation of related_names fail,
    or pkname validation fails.
    :param model_fields: dictionary of declared ormar model fields
    :type model_fields: Dict[str, ormar.Field]
    :param new_model:
    :type new_model: Model class
    :return: pkname, list of sqlalchemy columns
    :rtype: Tuple[Optional[str], List[sqlalchemy.Column]]
    """
    columns = []
    pkname = None
    for field_name, field in model_fields.items():
        field.owner = new_model
        if _is_through_model_not_set(field):
            field.create_default_through_model()
        if field.primary_key:
            pkname = check_pk_column_validity(field_name, field, pkname)
        if _is_db_field(field):
            columns.append(field.get_column(field.get_alias()))
    return pkname, columns


def _is_through_model_not_set(field: "BaseField") -> bool:
    """
    Alias to if check that verifies if through model was created.
    :param field: field to check
    :type field: "BaseField"
    :return: result of the check
    :rtype: bool
    """
    return field.is_multi and not field.through and not field.to.__class__ == ForwardRef


def _is_db_field(field: "BaseField") -> bool:
    """
    Alias to if check that verifies if field should be included in database.
    :param field: field to check
    :type field: "BaseField"
    :return: result of the check
    :rtype: bool
    """
    return (
        not field.pydantic_only
        and not field.virtual
        and not field.is_multi
        and not field.is_compound
    )


def populate_meta_tablename_columns_and_pk(
    name: str, new_model: Type["Model"]
) -> Type["Model"]:
    """
    Sets Model tablename if it's not already set in Meta.
    Default tablename if not present is class name lower + s (i.e. Bed becomes -> beds)

    Checks if Model's Meta have pkname and columns set.
    If not calls the sqlalchemy_columns_from_model_fields to populate
    columns from ormar.fields definitions.

    :raises ModelDefinitionError: if pkname is not present raises ModelDefinitionError.
    Each model has to have pk.

    :param name: name of the current Model
    :type name: str
    :param new_model: currently constructed Model
    :type new_model: ormar.models.metaclass.ModelMetaclass
    :return: Model with populated pkname and columns in Meta
    :rtype: ormar.models.metaclass.ModelMetaclass
    """
    tablename = name.lower() + "s"
    new_model.Meta.tablename = (
        new_model.Meta.tablename if hasattr(new_model.Meta, "tablename") else tablename
    )

    if not hasattr(new_model.Meta, "columns"):
        pkname, columns = sqlalchemy_columns_from_model_fields(
            new_model.Meta.model_fields, new_model
        )
        new_model.Meta.columns = columns
        new_model.Meta.pkname = pkname  # type: ignore

    if not new_model.pk_name and not new_model.has_pk_constraint:
        raise ormar.ModelDefinitionError("Table has to have a primary key.")

    if not new_model.Meta.orders_by:
        # by default we sort by pk name(s) if other option not provided
        new_model.Meta.orders_by.extend(new_model.pk_aliases_list)

    return new_model


def resolve_primary_key(new_model: Type["Model"], attrs: Dict) -> None:
    if new_model.has_pk_constraint:
        if new_model.Meta.pkname:
            raise ormar.ModelDefinitionError(
                "Table can only have one primary key!"
                "Primary key column and Constraint detected."
            )
        constraint = cast("PrimaryKeyConstraint", new_model.Meta.pk_constraint)
        constraint.owner = new_model
        constraint._resolve_column_aliases()

    if (
        not new_model.has_pk_constraint
        and new_model.pk_name not in attrs["__annotations__"]
        and new_model.Meta.pkname not in new_model.__fields__
    ):
        field_name = cast(str, new_model.pk_name)
        attrs["__annotations__"][field_name] = Optional[int]  # type: ignore
        attrs[field_name] = None
        new_model.__fields__[field_name] = get_pydantic_field(
            field_name=field_name, model=new_model
        )


def check_for_null_type_columns_from_forward_refs(meta: "ModelMeta") -> bool:
    """
    Check is any column is of NUllType() meaning it's empty column from ForwardRef

    :param meta: Meta class of the Model without sqlalchemy table constructed
    :type meta: Model class Meta
    :return: result of the check
    :rtype: bool
    """
    return not any(
        isinstance(col.type, sqlalchemy.sql.sqltypes.NullType) for col in meta.columns
    )


def populate_meta_sqlalchemy_table_if_required(meta: "ModelMeta") -> None:
    """
    Constructs sqlalchemy table out of columns and parameters set on Meta class.
    It populates name, metadata, columns and constraints.

    :param meta: Meta class of the Model without sqlalchemy table constructed
    :type meta: Model class Meta
    :return: class with populated Meta.table
    :rtype: Model class
    """
    if not hasattr(meta, "table") and check_for_null_type_columns_from_forward_refs(
        meta
    ):
        for constraint in meta.constraints:
            if isinstance(constraint, sqlalchemy.UniqueConstraint):
                constraint.name = (
                    f"uc_{meta.tablename}_"
                    f'{"_".join([str(col) for col in constraint._pending_colargs])}'
                )
        table = sqlalchemy.Table(
            meta.tablename, meta.metadata, *meta.columns, *meta.constraints
        )
        meta.table = table


def update_column_definition(
    model: Union[Type["Model"], Type["NewBaseModel"]], field: "ForeignKeyField"
) -> None:
    """
    Updates a column with a new type column based on updated parameters in FK fields.

    :param model: model on which columns needs to be updated
    :type model: Type["Model"]
    :param field: field with column definition that requires update
    :type field: ForeignKeyField
    :return: None
    :rtype: None
    """
    columns = model.Meta.columns
    fields_to_populate = [field.get_alias()]
    if field.is_compound:
        fields_to_populate = list(field.names.values())
    for ind, column in enumerate(columns):
        if column.name in fields_to_populate and isinstance(
            column.type, sqlalchemy.sql.sqltypes.NullType
        ):
            if not field.is_compound:
                new_column = field.get_column(column.name)
                columns[ind] = new_column
                break
            else:
                related_name = (field.get_reversed_names() or dict()).get(column.name)
                field_name = field.to.get_column_name_from_alias(
                    cast(str, related_name)
                )
                target_field = field.to.Meta.model_fields[field_name]
                new_column = target_field.get_column(column.name)
                columns[ind] = new_column


def remove_null_column_to_compound_models_fk(
    model: Union[Type["Model"], Type["NewBaseModel"]]
) -> None:
    """
    Remove nulltype fields if compose keys created all new columns.
    Nulltype is left if all composite pks are created and the relation field
    is not used to create actual db column

    :param model: model on which columns needs to be updated
    :type model: Type["Model"]
    :param field: field with column definition that requires update
    :type field: ForeignKeyField
    :return: None
    :rtype: None
    """
    model.Meta.columns = [
        col
        for col in model.Meta.columns
        if not isinstance(col.type, sqlalchemy.sql.sqltypes.NullType)
    ]
