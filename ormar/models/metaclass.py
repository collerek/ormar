import copy
import logging
import warnings
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    TYPE_CHECKING,
    Tuple,
    Type,
    Union,
)

import databases
import pydantic
import sqlalchemy
from pydantic import BaseConfig
from pydantic.fields import FieldInfo, ModelField
from pydantic.utils import lenient_issubclass
from sqlalchemy.sql.schema import ColumnCollectionConstraint

import ormar  # noqa I100
from ormar import ForeignKey, Integer, ModelDefinitionError  # noqa I100
from ormar.fields import BaseField
from ormar.fields.foreign_key import ForeignKeyField
from ormar.fields.many_to_many import ManyToMany, ManyToManyField
from ormar.models.quick_access_views import quick_access_set
from ormar.queryset import QuerySet
from ormar.relations.alias_manager import AliasManager
from ormar.signals import Signal, SignalEmitter

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model

alias_manager = AliasManager()
PARSED_FIELDS_KEY = "__parsed_fields__"
CONFIG_KEY = "Config"


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
    property_fields: Set
    signals: SignalEmitter
    abstract: bool


def register_relation_on_build_new(new_model: Type["Model"], field_name: str) -> None:
    alias_manager.add_relation_type_new(new_model, field_name)


def register_many_to_many_relation_on_build_new(
        new_model: Type["Model"], field: Type[ManyToManyField]
) -> None:
    alias_manager.add_relation_type_new(
        field.through, new_model.get_name(), is_multi=True
    )
    alias_manager.add_relation_type_new(
        field.through, field.to.get_name(), is_multi=True
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
            child,
            through=model_field.through,
            name=child_model_name,
            virtual=True,
            related_name=model_field.name,
        )
        # register foreign keys on through model
        adjust_through_many_to_many_model(model, child, model_field, child_model_name)
    else:
        model.Meta.model_fields[child_model_name] = ForeignKey(
            child,
            real_name=child_model_name,
            virtual=True,
            related_name=model_field.name,
        )


def adjust_through_many_to_many_model(
        model: Type["Model"],
        child: Type["Model"],
        model_field: Type[ManyToManyField],
        child_model_name: str,
) -> None:
    model_field.through.Meta.model_fields[model.get_name()] = ForeignKey(
        model, real_name=model.get_name(), ondelete="CASCADE"
    )
    model_field.through.Meta.model_fields[child.get_name()] = ForeignKey(
        child, real_name=child.get_name(), ondelete="CASCADE"
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


def get_pydantic_field(field_name: str, model: Type["Model"]) -> "ModelField":
    return ModelField(
        name=field_name,
        type_=model.Meta.model_fields[field_name].__type__,  # type: ignore
        model_config=model.__config__,
        required=not model.Meta.model_fields[field_name].nullable,
        class_validators={},
    )


def create_and_append_m2m_fk(
        model: Type["Model"], model_field: Type[ManyToManyField]
) -> None:
    column = sqlalchemy.Column(
        model.get_name(),
        model.Meta.table.columns.get(model.get_column_alias(model.Meta.pkname)).type,
        sqlalchemy.schema.ForeignKey(
            model.Meta.tablename + "." + model.get_column_alias(model.Meta.pkname),
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


def validate_related_names_in_relations(
        model_fields: Dict, new_model: Type["Model"]
) -> None:
    already_registered: Dict[str, List[Optional[str]]] = dict()
    for field in model_fields.values():
        if issubclass(field, ForeignKeyField):
            previous_related_names = already_registered.setdefault(field.to, [])
            if field.related_name in previous_related_names:
                raise ModelDefinitionError(
                    f"Multiple fields declared on {new_model.get_name(lower=False)} "
                    f"model leading to {field.to.get_name(lower=False)} model without "
                    f"related_name property set. \nThere can be only one relation with "
                    f"default/empty name: '{new_model.get_name() + 's'}'"
                    f"\nTip: provide different related_name for FK and/or M2M fields"
                )
            else:
                previous_related_names.append(field.related_name)


def sqlalchemy_columns_from_model_fields(
        model_fields: Dict, new_model: Type["Model"]
) -> Tuple[Optional[str], List[sqlalchemy.Column]]:
    columns = []
    pkname = None
    if len(model_fields.keys()) == 0:
        model_fields["id"] = Integer(name="id", primary_key=True)
        logging.warning(
            "Table {table_name} had no fields so auto "
            "Integer primary key named `id` created."
        )
    validate_related_names_in_relations(model_fields, new_model)
    for field_name, field in model_fields.items():
        if field.primary_key:
            pkname = check_pk_column_validity(field_name, field, pkname)
        if (
                not field.pydantic_only
                and not field.virtual
                and not issubclass(field, ManyToManyField)
        ):
            columns.append(field.get_column(field.get_alias()))
    return pkname, columns


def register_relation_in_alias_manager_new(
        new_model: Type["Model"], field: Type[ForeignKeyField], field_name: str
) -> None:
    if issubclass(field, ManyToManyField):
        register_many_to_many_relation_on_build_new(new_model=new_model, field=field)
    elif issubclass(field, ForeignKeyField):
        register_relation_on_build_new(new_model=new_model, field_name=field_name)


def populate_default_pydantic_field_value(
        ormar_field: Type[BaseField], field_name: str, attrs: dict
) -> dict:
    curr_def_value = attrs.get(field_name, ormar.Undefined)
    if lenient_issubclass(curr_def_value, ormar.fields.BaseField):
        curr_def_value = ormar.Undefined
    if curr_def_value is None:
        attrs[field_name] = ormar_field.convert_to_pydantic_field_info(allow_null=True)
    else:
        attrs[field_name] = ormar_field.convert_to_pydantic_field_info()
    return attrs


def populate_pydantic_default_values(attrs: Dict) -> Tuple[Dict, Dict]:
    model_fields = {}
    potential_fields = {
        k: v
        for k, v in attrs["__annotations__"].items()
        if lenient_issubclass(v, BaseField)
    }
    if potential_fields:
        warnings.warn(
            "Using ormar.Fields as type Model annotation has been deprecated,"
            " check documentation of current version",
            DeprecationWarning,
        )

    potential_fields.update(get_potential_fields(attrs))
    for field_name, field in potential_fields.items():
        field.name = field_name
        attrs = populate_default_pydantic_field_value(field, field_name, attrs)
        model_fields[field_name] = field
        attrs["__annotations__"][field_name] = (
            field.__type__ if not field.nullable else Optional[field.__type__]
        )
    return attrs, model_fields


def extract_annotations_and_default_vals(attrs: dict) -> Tuple[Dict, Dict]:
    key = "__annotations__"
    attrs[key] = attrs.get(key, {})
    attrs, model_fields = populate_pydantic_default_values(attrs)
    return attrs, model_fields


def populate_meta_tablename_columns_and_pk(
        name: str, new_model: Type["Model"]
) -> Type["Model"]:
    tablename = name.lower() + "s"
    new_model.Meta.tablename = (
        new_model.Meta.tablename if hasattr(new_model.Meta, "tablename") else tablename
    )
    pkname: Optional[str]

    if hasattr(new_model.Meta, "columns"):
        columns = new_model.Meta.table.columns
        pkname = new_model.Meta.pkname
    else:
        pkname, columns = sqlalchemy_columns_from_model_fields(
            new_model.Meta.model_fields, new_model
        )

    if pkname is None:
        raise ModelDefinitionError("Table has to have a primary key.")

    new_model.Meta.columns = columns
    new_model.Meta.pkname = pkname
    return new_model


def populate_meta_sqlalchemy_table_if_required(
        new_model: Type["Model"],
) -> Type["Model"]:
    """
    Constructs sqlalchemy table out of columns and parameters set on Meta class.
    It populates name, metadata, columns and constraints.

    :param new_model: class without sqlalchemy table constructed
    :type new_model: Model class
    :return: class with populated Meta.table
    :rtype: Model class
    """
    if not hasattr(new_model.Meta, "table"):
        new_model.Meta.table = sqlalchemy.Table(
            new_model.Meta.tablename,
            new_model.Meta.metadata,
            *new_model.Meta.columns,
            *new_model.Meta.constraints,
        )
    return new_model


def get_pydantic_base_orm_config() -> Type[BaseConfig]:
    """
    Returns empty pydantic Config with orm_mode set to True.

    :return: empty default config with orm_mode set.
    :rtype: pydantic Config
    """

    class Config(BaseConfig):
        orm_mode = True

    return Config


def check_if_field_has_choices(field: Type[BaseField]) -> bool:
    """
    Checks if given field has choices populated.
    A if it has one, a validator for this field needs to be attached.

    :param field: ormar field to check
    :type field: BaseField
    :return: result of the check
    :rtype: bool
    """
    return hasattr(field, "choices") and bool(field.choices)


def choices_validator(cls: Type["Model"], values: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validator that is attached to pydantic model pre root validators.
    Validator checks if field value is in field.choices list.

    :raises: ValueError if field value is outside of allowed choices.
    :param cls: constructed class
    :type cls: Model class
    :param values: dictionary of field values (pydantic side)
    :type values: Dict[str, Any]
    :return: values if pass validation, otherwise exception is raised
    :rtype: Dict[str, Any]
    """
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


def populate_choices_validators(model: Type["Model"]) -> None:  # noqa CCR001
    """
    Checks if Model has any fields with choices set.
    If yes it adds choices validation into pre root validators.

    :param model: newly constructed Model
    :type model: Model class
    """
    if not meta_field_not_set(model=model, field_name="model_fields"):
        for _, field in model.Meta.model_fields.items():
            if check_if_field_has_choices(field):
                validators = getattr(model, "__pre_root_validators__", [])
                if choices_validator not in validators:
                    validators.append(choices_validator)
                    model.__pre_root_validators__ = validators


def populate_default_options_values(
        new_model: Type["Model"], model_fields: Dict
) -> None:
    """
    Sets all optional Meta values to it's defaults
    and set model_fields that were already previously extracted.

    Here should live all options that are not overwritten/set for all models.

    Current options are:
    * constraints = []
    * abstract = False

    :param new_model: newly constructed Model
    :type new_model: Model class
    :param model_fields:
    :type model_fields: Union[Dict[str, type], Dict]
    """
    if not hasattr(new_model.Meta, "constraints"):
        new_model.Meta.constraints = []
    if not hasattr(new_model.Meta, "model_fields"):
        new_model.Meta.model_fields = model_fields
    if not hasattr(new_model.Meta, "abstract"):
        new_model.Meta.abstract = False


def add_cached_properties(new_model: Type["Model"]) -> None:
    """
    Sets cached properties for both pydantic and ormar models.

    Quick access fields are fields grabbed in getattribute to skip all checks.

    Related fields and names are populated to None as they can change later.
    When children models are constructed they can modify parent to register itself.

    All properties here are used as "cache" to not recalculate them constantly.

    :param new_model: newly constructed Model
    :type new_model: Model class
    """
    new_model._quick_access_fields = quick_access_set
    new_model._related_names = None
    new_model._related_fields = None
    new_model._pydantic_fields = {name for name in new_model.__fields__}


def meta_field_not_set(model: Type["Model"], field_name: str) -> bool:
    """
    Checks if field with given name is already present in model.Meta.
    Then check if it's set to something truthful
    (in practice meaning not None, as it's non or ormar Field only).

    :param model: newly constructed model
    :type model: Model class
    :param field_name: name of the ormar field
    :type field_name: str
    :return: result of the check
    :rtype: bool
    """
    return not hasattr(model.Meta, field_name) or not getattr(model.Meta, field_name)


def add_property_fields(new_model: Type["Model"], attrs: Dict) -> None:  # noqa: CCR001
    """
    Checks class namespace for properties or functions with __property_field__.
    If attribute have __property_field__ it was decorated with @property_field.

    Functions like this are exposed in dict() (therefore also fastapi result).
    Names of property fields are cached for quicker access / extraction.

    :param new_model: newly constructed model
    :type new_model: Model class
    :param attrs:
    :type attrs: Dict[str, str]
    """
    props = set()
    for var_name, value in attrs.items():
        if isinstance(value, property):
            value = value.fget
        field_config = getattr(value, "__property_field__", None)
        if field_config:
            props.add(var_name)

    if meta_field_not_set(model=new_model, field_name="property_fields"):
        new_model.Meta.property_fields = props
    else:
        new_model.Meta.property_fields = new_model.Meta.property_fields.union(props)


def register_signals(new_model: Type["Model"]) -> None:  # noqa: CCR001
    """
    Registers on model's SignalEmmiter and sets pre defined signals.
    Predefined signals are (pre/post) + (save/update/delete).

    Signals are emitted in both model own methods and in selected queryset ones.

    :param new_model: newly constructed model
    :type new_model: Model class
    """
    if meta_field_not_set(model=new_model, field_name="signals"):
        signals = SignalEmitter()
        signals.pre_save = Signal()
        signals.pre_update = Signal()
        signals.pre_delete = Signal()
        signals.post_save = Signal()
        signals.post_update = Signal()
        signals.post_delete = Signal()
        new_model.Meta.signals = signals


def get_potential_fields(attrs: Dict) -> Dict:
    """
    Gets all the fields in current class namespace that are Fields.

    :param attrs: current class namespace
    :type attrs: Dict
    :return: extracted fields that are ormar Fields
    :rtype: Dict
    """
    return {k: v for k, v in attrs.items() if lenient_issubclass(v, BaseField)}


def check_conflicting_fields(
        new_fields: Set,
        attrs: Dict,
        base_class: type,
        curr_class: type,
        previous_fields: Set = None,
) -> None:
    """
    You cannot redefine fields with same names in inherited classes.
    Ormar will raise an exception if it encounters a field that is an ormar
    Field and at the same time was already declared in one of base classes.

    :param previous_fields: set of names of fields defined in base model
    :type previous_fields: Set[str]
    :param new_fields: set of names of fields defined in current model
    :type new_fields: Set[str]
    :param attrs: namespace of current class
    :type attrs: Dict
    :param base_class: one of the parent classes
    :type base_class: Model or model parent class
    :param curr_class: current constructed class
    :type curr_class: Model or model parent class
    """
    if not previous_fields:
        previous_fields = set({k for k, v in attrs.items() if isinstance(v, FieldInfo)})
    overwrite = new_fields.intersection(previous_fields)

    if overwrite:
        raise ModelDefinitionError(
            f"Model {curr_class} redefines the fields: "
            f"{overwrite} already defined in {base_class}!"
        )


def update_attrs_and_fields(
        attrs: Dict,
        new_attrs: Dict,
        model_fields: Dict,
        new_model_fields: Dict,
        new_fields: Set,
) -> None:
    """
    Updates __annotations__, values of model fields (so pydantic FieldInfos)
    as well as model.Meta.model_fields definitions from parents.

    :param attrs: new namespace for class being constructed
    :type attrs: Dict
    :param new_attrs: part of the namespace extracted from parent class
    :type new_attrs: Dict
    :param model_fields: ormar fields in defined in current class
    :type model_fields: Dict[str, BaseField]
    :param new_model_fields: ormar fields defined in parent classes
    :type new_model_fields: Dict[str, BaseField]
    :param new_fields: set of new fields names
    :type new_fields: Set[str]
    """
    key = "__annotations__"
    attrs[key].update(new_attrs[key])
    attrs.update({name: new_attrs[name] for name in new_fields})
    model_fields.update(new_model_fields)


def update_attrs_from_base_meta(  # noqa: CCR001
        base_class: "Model", attrs: Dict,
) -> None:
    """
    Updates Meta parameters in child from parent if needed.

    :param base_class: one of the parent classes
    :type base_class: Model or model parent class
    :param attrs: new namespace for class being constructed
    :type attrs: Dict
    """
    params_to_update = ["metadata", "database", "constraints"]
    for param in params_to_update:
        current_value = attrs.get("Meta", {}).__dict__.get(param, ormar.Undefined)
        parent_value = (
            base_class.Meta.__dict__.get(param) if hasattr(base_class, "Meta") else None
        )
        if parent_value:
            if param == "constraints":
                parent_value = [
                    ormar.UniqueColumns(*x._pending_colargs) for x in parent_value
                ]
            if isinstance(current_value, list):
                current_value.extend(parent_value)
            else:
                setattr(attrs["Meta"], param, parent_value)


def extract_from_parents_definition(  # noqa: CCR001
        base_class: type,
        curr_class: type,
        attrs: Dict,
        model_fields: Dict[
            str, Union[Type[BaseField], Type[ForeignKeyField], Type[ManyToManyField]]
        ],
) -> Tuple[Dict, Dict]:
    """
    Extracts fields from base classes if they have valid oramr fields.

    If model was already parsed -> fields definitions need to be removed from class
    cause pydantic complains about field re-definition so after first child
    we need to extract from __parsed_fields__ not the class itself.

    If the class is parsed first time annotations and field definition is parsed
    from the class.__dict__.

    If the class is a ormar.Model it is skipped.

    :param base_class: one of the parent classes
    :type base_class: Model or model parent class
    :param curr_class: current constructed class
    :type curr_class: Model or model parent class
    :param attrs: new namespace for class being constructed
    :type attrs: Dict
    :param model_fields: ormar fields in defined in current class
    :type model_fields: Dict[str, BaseField]
    :return: updated attrs and model_fields
    :rtype: Tuple[Dict, Dict]
    """
    if hasattr(base_class, "Meta"):
        if attrs.get("Meta"):
            new_fields = set(base_class.Meta.model_fields.keys())  # type: ignore
            previous_fields = set(
                {k for k, v in attrs.items() if isinstance(v, FieldInfo)}
            )
            check_conflicting_fields(
                new_fields=new_fields,
                attrs=attrs,
                base_class=base_class,
                curr_class=curr_class,
                previous_fields=previous_fields,
            )
            if previous_fields and not base_class.Meta.abstract:  # type: ignore
                raise ModelDefinitionError(
                    f"{curr_class.__name__} cannot inherit "
                    f"from non abstract class {base_class.__name__}"
                )
            update_attrs_from_base_meta(
                base_class=base_class,  # type: ignore
                attrs=attrs,
            )
            parent_fields = dict()
            table_name = attrs.get("Meta").tablename if hasattr(attrs.get("Meta"), "tablename") else attrs.get(
                '__name__').lower() + 's'
            for field_name, field in base_class.Meta.model_fields.items():
                if issubclass(field, ForeignKeyField) and field.related_name:
                    copy_field = type(field.__name__, (field,), dict(field.__dict__))
                    copy_field.related_name = field.related_name + '_' + table_name
                    parent_fields[field_name] = copy_field
                else:
                    parent_fields[field_name] = field

            model_fields.update(parent_fields)  # type: ignore
        return attrs, model_fields

    key = "__annotations__"
    if hasattr(base_class, PARSED_FIELDS_KEY):
        # model was already parsed -> fields definitions need to be removed from class
        # cause pydantic complains about field re-definition so after first child
        # we need to extract from __parsed_fields__ not the class itself
        new_attrs, new_model_fields = getattr(base_class, PARSED_FIELDS_KEY)

        new_fields = set(new_model_fields.keys())
        check_conflicting_fields(
            new_fields=new_fields,
            attrs=attrs,
            base_class=base_class,
            curr_class=curr_class,
        )

        update_attrs_and_fields(
            attrs=attrs,
            new_attrs=new_attrs,
            model_fields=model_fields,
            new_model_fields=new_model_fields,
            new_fields=new_fields,
        )
        return attrs, model_fields

    potential_fields = get_potential_fields(base_class.__dict__)
    if potential_fields:
        # parent model has ormar fields defined and was not parsed before
        new_attrs = {key: base_class.__dict__.get(key, {})}
        new_attrs.update(potential_fields)

        new_fields = set(potential_fields.keys())
        check_conflicting_fields(
            new_fields=new_fields,
            attrs=attrs,
            base_class=base_class,
            curr_class=curr_class,
        )
        for name in new_fields:
            delattr(base_class, name)

        new_attrs, new_model_fields = extract_annotations_and_default_vals(new_attrs)
        setattr(base_class, PARSED_FIELDS_KEY, (new_attrs, new_model_fields))

        update_attrs_and_fields(
            attrs=attrs,
            new_attrs=new_attrs,
            model_fields=model_fields,
            new_model_fields=new_model_fields,
            new_fields=new_fields,
        )
    return attrs, model_fields


class ModelMetaclass(pydantic.main.ModelMetaclass):
    def __new__(  # type: ignore # noqa: CCR001
            mcs: "ModelMetaclass", name: str, bases: Any, attrs: dict
    ) -> "ModelMetaclass":
        attrs["Config"] = get_pydantic_base_orm_config()
        attrs["__name__"] = name
        attrs, model_fields = extract_annotations_and_default_vals(attrs)
        for base in reversed(bases):
            attrs, model_fields = extract_from_parents_definition(
                base_class=base, curr_class=mcs, attrs=attrs, model_fields=model_fields
            )
        new_model = super().__new__(  # type: ignore
            mcs, name, bases, attrs
        )

        add_cached_properties(new_model)

        if hasattr(new_model, "Meta"):
            populate_default_options_values(new_model, model_fields)
            add_property_fields(new_model, attrs)
            register_signals(new_model=new_model)
            populate_choices_validators(new_model)

            if not new_model.Meta.abstract:
                new_model = populate_meta_tablename_columns_and_pk(name, new_model)
                new_model = populate_meta_sqlalchemy_table_if_required(new_model)
                expand_reverse_relationships(new_model)
                for field_name, field in new_model.Meta.model_fields.items():
                    register_relation_in_alias_manager_new(new_model, field, field_name)

                if new_model.Meta.pkname not in attrs["__annotations__"]:
                    field_name = new_model.Meta.pkname
                    attrs["__annotations__"][field_name] = Optional[int]  # type: ignore
                    attrs[field_name] = None
                    new_model.__fields__[field_name] = get_pydantic_field(
                        field_name=field_name, model=new_model
                    )
                new_model.Meta.alias_manager = alias_manager
                new_model.objects = QuerySet(new_model)

        return new_model
