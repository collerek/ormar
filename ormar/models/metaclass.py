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
    cast,
)

import databases
import pydantic
import sqlalchemy
from sqlalchemy.sql.schema import ColumnCollectionConstraint

import ormar  # noqa I100
import ormar.fields.constraints
from ormar import ModelDefinitionError  # noqa I100
from ormar.exceptions import ModelError
from ormar.fields import BaseField
from ormar.fields.foreign_key import ForeignKeyField
from ormar.fields.many_to_many import ManyToManyField
from ormar.models.descriptors import (
    JsonDescriptor,
    PkDescriptor,
    PropertyDescriptor,
    PydanticDescriptor,
    RelationDescriptor,
)
from ormar.models.descriptors.descriptors import BytesDescriptor
from ormar.models.helpers import (
    alias_manager,
    check_required_meta_parameters,
    expand_reverse_relationships,
    extract_annotations_and_default_vals,
    get_potential_fields,
    get_pydantic_field,
    merge_or_generate_pydantic_config,
    meta_field_not_set,
    populate_choices_validators,
    populate_default_options_values,
    populate_meta_sqlalchemy_table_if_required,
    populate_meta_tablename_columns_and_pk,
    register_relation_in_alias_manager,
    remove_excluded_parent_fields,
    sqlalchemy_columns_from_model_fields,
)
from ormar.models.quick_access_views import quick_access_set
from ormar.models.utils import Extra
from ormar.queryset import FieldAccessor, QuerySet
from ormar.relations.alias_manager import AliasManager
from ormar.signals import Signal, SignalEmitter

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model
    from ormar.models import T

CONFIG_KEY = "Config"
PARSED_FIELDS_KEY = "__parsed_fields__"


class ModelMeta:
    """
    Class used for type hinting.
    Users can subclass this one for convenience but it's not required.
    The only requirement is that ormar.Model has to have inner class with name Meta.
    """

    tablename: str
    table: sqlalchemy.Table
    metadata: sqlalchemy.MetaData
    database: databases.Database
    columns: List[sqlalchemy.Column]
    constraints: List[ColumnCollectionConstraint]
    pkname: str
    model_fields: Dict[str, Union[BaseField, ForeignKeyField, ManyToManyField]]
    alias_manager: AliasManager
    property_fields: Set
    signals: SignalEmitter
    abstract: bool
    requires_ref_update: bool
    orders_by: List[str]
    exclude_parent_fields: List[str]
    extra: Extra
    queryset_class: Type[QuerySet]


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
    new_model._through_names = None
    new_model._related_fields = None
    new_model._pydantic_fields = {name for name in new_model.__fields__}
    new_model._json_fields = set()
    new_model._bytes_fields = set()


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
        signals.pre_relation_add = Signal()
        signals.post_relation_add = Signal()
        signals.pre_relation_remove = Signal()
        signals.post_relation_remove = Signal()
        signals.post_bulk_update = Signal()
        new_model.Meta.signals = signals


def verify_constraint_names(
    base_class: "Model", model_fields: Dict, parent_value: List
) -> None:
    """
    Verifies if redefined fields that are overwritten in subclasses did not remove
    any name of the column that is used in constraint as it will fail in sqlalchemy
    Table creation.

    :param base_class: one of the parent classes
    :type base_class: Model or model parent class
    :param model_fields: ormar fields in defined in current class
    :type model_fields: Dict[str, BaseField]
    :param parent_value: list of base class constraints
    :type parent_value: List
    """
    new_aliases = {x.name: x.get_alias() for x in model_fields.values()}
    old_aliases = {x.name: x.get_alias() for x in base_class.Meta.model_fields.values()}
    old_aliases.update(new_aliases)
    constraints_columns = [x._pending_colargs for x in parent_value]
    for column_set in constraints_columns:
        if any(x not in old_aliases.values() for x in column_set):
            raise ModelDefinitionError(
                f"Unique columns constraint "
                f"{column_set} "
                f"has column names "
                f"that are not in the model fields."
                f"\n Check columns redefined in subclasses "
                f"to verify that they have proper 'name' set."
            )


def update_attrs_from_base_meta(  # noqa: CCR001
    base_class: "Model", attrs: Dict, model_fields: Dict
) -> None:
    """
    Updates Meta parameters in child from parent if needed.

    :param base_class: one of the parent classes
    :type base_class: Model or model parent class
    :param attrs: new namespace for class being constructed
    :type attrs: Dict
    :param model_fields: ormar fields in defined in current class
    :type model_fields: Dict[str, BaseField]
    """

    params_to_update = ["metadata", "database", "constraints"]
    for param in params_to_update:
        current_value = attrs.get("Meta", {}).__dict__.get(param, ormar.Undefined)
        parent_value = (
            base_class.Meta.__dict__.get(param) if hasattr(base_class, "Meta") else None
        )
        if parent_value:
            if param == "constraints":
                verify_constraint_names(
                    base_class=base_class,
                    model_fields=model_fields,
                    parent_value=parent_value,
                )
                parent_value = [
                    ormar.fields.constraints.UniqueColumns(*x._pending_colargs)
                    for x in parent_value
                ]
            if isinstance(current_value, list):
                current_value.extend(parent_value)
            else:
                setattr(attrs["Meta"], param, parent_value)


def copy_and_replace_m2m_through_model(  # noqa: CFQ002
    field: ManyToManyField,
    field_name: str,
    table_name: str,
    parent_fields: Dict,
    attrs: Dict,
    meta: ModelMeta,
    base_class: Type["Model"],
) -> None:
    """
    Clones class with Through model for m2m relations, appends child name to the name
    of the cloned class.

    Clones non foreign keys fields from parent model, the same with database columns.

    Modifies related_name with appending child table name after '_'

    For table name, the table name of child is appended after '_'.

    Removes the original sqlalchemy table from metadata if it was not removed.

    :param base_class: base class model
    :type base_class: Type["Model"]
    :param field: field with relations definition
    :type field: ManyToManyField
    :param field_name: name of the relation field
    :type field_name: str
    :param table_name: name of the table
    :type table_name: str
    :param parent_fields: dictionary of fields to copy to new models from parent
    :type parent_fields: Dict
    :param attrs: new namespace for class being constructed
    :type attrs: Dict
    :param meta: metaclass of currently created model
    :type meta: ModelMeta
    """
    Field: Type[BaseField] = type(  # type: ignore
        field.__class__.__name__, (ManyToManyField, BaseField), {}
    )
    copy_field = Field(**dict(field.__dict__))
    related_name = field.related_name + "_" + table_name
    copy_field.related_name = related_name  # type: ignore

    through_class = field.through
    if not through_class:
        field.owner = base_class
        field.create_default_through_model()
        through_class = field.through
    new_meta: ormar.ModelMeta = type(  # type: ignore
        "Meta", (), dict(through_class.Meta.__dict__)
    )
    copy_name = through_class.__name__ + attrs.get("__name__", "")
    copy_through = type(copy_name, (ormar.Model,), {"Meta": new_meta})
    new_meta.tablename += "_" + meta.tablename
    # create new table with copied columns but remove foreign keys
    # they will be populated later in expanding reverse relation
    if hasattr(new_meta, "table"):
        del new_meta.table
    new_meta.model_fields = {
        name: field
        for name, field in new_meta.model_fields.items()
        if not field.is_relation
    }
    _, columns = sqlalchemy_columns_from_model_fields(
        new_meta.model_fields, copy_through
    )  # type: ignore
    new_meta.columns = columns
    populate_meta_sqlalchemy_table_if_required(new_meta)
    copy_field.through = copy_through

    parent_fields[field_name] = copy_field

    if through_class.Meta.table in through_class.Meta.metadata:
        through_class.Meta.metadata.remove(through_class.Meta.table)


def copy_data_from_parent_model(  # noqa: CCR001
    base_class: Type["Model"],
    curr_class: type,
    attrs: Dict,
    model_fields: Dict[str, Union[BaseField, ForeignKeyField, ManyToManyField]],
) -> Tuple[Dict, Dict]:
    """
    Copy the key parameters [database, metadata, property_fields and constraints]
    and fields from parent models. Overwrites them if needed.

    Only abstract classes can be subclassed.

    Since relation fields requires different related_name for different children


    :raises ModelDefinitionError: if non abstract model is subclassed
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
    if attrs.get("Meta"):
        if model_fields and not base_class.Meta.abstract:  # type: ignore
            raise ModelDefinitionError(
                f"{curr_class.__name__} cannot inherit "
                f"from non abstract class {base_class.__name__}"
            )
        update_attrs_from_base_meta(
            base_class=base_class,  # type: ignore
            attrs=attrs,
            model_fields=model_fields,
        )
        parent_fields: Dict = dict()
        meta = attrs.get("Meta")
        if not meta:  # pragma: no cover
            raise ModelDefinitionError(
                f"Model {curr_class.__name__} declared without Meta"
            )
        table_name = (
            meta.tablename
            if hasattr(meta, "tablename") and meta.tablename
            else attrs.get("__name__", "").lower() + "s"
        )
        for field_name, field in base_class.Meta.model_fields.items():
            if (
                hasattr(meta, "exclude_parent_fields")
                and field_name in meta.exclude_parent_fields
            ):
                continue
            if field.is_multi:
                field = cast(ManyToManyField, field)
                copy_and_replace_m2m_through_model(
                    field=field,
                    field_name=field_name,
                    table_name=table_name,
                    parent_fields=parent_fields,
                    attrs=attrs,
                    meta=meta,
                    base_class=base_class,  # type: ignore
                )

            elif field.is_relation and field.related_name:
                Field = type(  # type: ignore
                    field.__class__.__name__, (ForeignKeyField, BaseField), {}
                )
                copy_field = Field(**dict(field.__dict__))
                related_name = field.related_name + "_" + table_name
                copy_field.related_name = related_name  # type: ignore
                parent_fields[field_name] = copy_field
            else:
                parent_fields[field_name] = field

        parent_fields.update(model_fields)  # type: ignore
        model_fields = parent_fields
    return attrs, model_fields


def extract_from_parents_definition(  # noqa: CCR001
    base_class: type,
    curr_class: type,
    attrs: Dict,
    model_fields: Dict[str, Union[BaseField, ForeignKeyField, ManyToManyField]],
) -> Tuple[Dict, Dict]:
    """
    Extracts fields from base classes if they have valid ormar fields.

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
        base_class = cast(Type["Model"], base_class)
        return copy_data_from_parent_model(
            base_class=base_class,
            curr_class=curr_class,
            attrs=attrs,
            model_fields=model_fields,
        )

    key = "__annotations__"
    if hasattr(base_class, PARSED_FIELDS_KEY):
        # model was already parsed -> fields definitions need to be removed from class
        # cause pydantic complains about field re-definition so after first child
        # we need to extract from __parsed_fields__ not the class itself
        new_attrs, new_model_fields = getattr(base_class, PARSED_FIELDS_KEY)

        new_fields = set(new_model_fields.keys())
        model_fields = update_attrs_and_fields(
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
        new_attrs = {key: {k: v for k, v in base_class.__dict__.get(key, {}).items()}}
        new_attrs.update(potential_fields)

        new_fields = set(potential_fields.keys())
        for name in new_fields:
            delattr(base_class, name)

        new_attrs, new_model_fields = extract_annotations_and_default_vals(new_attrs)
        setattr(base_class, PARSED_FIELDS_KEY, (new_attrs, new_model_fields))
        model_fields = update_attrs_and_fields(
            attrs=attrs,
            new_attrs=new_attrs,
            model_fields=model_fields,
            new_model_fields=new_model_fields,
            new_fields=new_fields,
        )
    return attrs, model_fields


def update_attrs_and_fields(
    attrs: Dict,
    new_attrs: Dict,
    model_fields: Dict,
    new_model_fields: Dict,
    new_fields: Set,
) -> Dict:
    """
    Updates __annotations__, values of model fields (so pydantic FieldInfos)
    as well as model.Meta.model_fields definitions from parents.

    :param attrs: new namespace for class being constructed
    :type attrs: Dict
    :param new_attrs: related of the namespace extracted from parent class
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
    updated_model_fields = {k: v for k, v in new_model_fields.items()}
    updated_model_fields.update(model_fields)
    return updated_model_fields


def add_field_descriptor(
    name: str, field: "BaseField", new_model: Type["Model"]
) -> None:
    """
    Sets appropriate descriptor for each model field.
    There are 5 main types of descriptors, for bytes, json, pure pydantic fields,
    and 2 ormar ones - one for relation and one for pk shortcut

    :param name: name of the field
    :type name: str
    :param field: model field to add descriptor for
    :type field: BaseField
    :param new_model: model with fields
    :type new_model: Type["Model]
    """
    if field.is_relation:
        setattr(new_model, name, RelationDescriptor(name=name))
    elif field.__type__ == pydantic.Json:
        setattr(new_model, name, JsonDescriptor(name=name))
    elif field.__type__ == bytes:
        setattr(new_model, name, BytesDescriptor(name=name))
    else:
        setattr(new_model, name, PydanticDescriptor(name=name))


class ModelMetaclass(pydantic.main.ModelMetaclass):
    def __new__(  # type: ignore # noqa: CCR001
        mcs: "ModelMetaclass", name: str, bases: Any, attrs: dict
    ) -> "ModelMetaclass":
        """
        Metaclass used by ormar Models that performs configuration
        and build of ormar Models.


        Sets pydantic configuration.
        Extract model_fields and convert them to pydantic FieldInfo,
        updates class namespace.

        Extracts settings and fields from parent classes.
        Fetches methods decorated with @property_field decorator
        to expose them later in dict().

        Construct parent pydantic Metaclass/ Model.

        If class has Meta class declared (so actual ormar Models) it also:

        * populate sqlalchemy columns, pkname and tables from model_fields
        * register reverse relationships on related models
        * registers all relations in alias manager that populates table_prefixes
        * exposes alias manager on each Model
        * creates QuerySet for each model and exposes it on a class

        :param name: name of current class
        :type name: str
        :param bases: base classes
        :type bases: Tuple
        :param attrs: class namespace
        :type attrs: Dict
        """
        merge_or_generate_pydantic_config(attrs=attrs, name=name)
        attrs["__name__"] = name
        attrs, model_fields = extract_annotations_and_default_vals(attrs)
        for base in reversed(bases):
            mod = base.__module__
            if mod.startswith("ormar.models.") or mod.startswith("pydantic."):
                continue
            attrs, model_fields = extract_from_parents_definition(
                base_class=base, curr_class=mcs, attrs=attrs, model_fields=model_fields
            )
        new_model = super().__new__(mcs, name, bases, attrs)  # type: ignore

        add_cached_properties(new_model)

        if hasattr(new_model, "Meta"):
            populate_default_options_values(new_model, model_fields)
            check_required_meta_parameters(new_model)
            add_property_fields(new_model, attrs)
            register_signals(new_model=new_model)
            populate_choices_validators(new_model)

            if not new_model.Meta.abstract:
                new_model = populate_meta_tablename_columns_and_pk(name, new_model)
                populate_meta_sqlalchemy_table_if_required(new_model.Meta)
                expand_reverse_relationships(new_model)
                # TODO: iterate only related fields
                for field_name, field in new_model.Meta.model_fields.items():
                    register_relation_in_alias_manager(field=field)
                    add_field_descriptor(
                        name=field_name, field=field, new_model=new_model
                    )

                if (
                    new_model.Meta.pkname
                    and new_model.Meta.pkname not in attrs["__annotations__"]
                    and new_model.Meta.pkname not in new_model.__fields__
                ):
                    field_name = new_model.Meta.pkname
                    attrs["__annotations__"][field_name] = Optional[int]  # type: ignore
                    attrs[field_name] = None
                    new_model.__fields__[field_name] = get_pydantic_field(
                        field_name=field_name, model=new_model
                    )
                new_model.Meta.alias_manager = alias_manager

                for item in new_model.Meta.property_fields:
                    function = getattr(new_model, item)
                    setattr(
                        new_model,
                        item,
                        PropertyDescriptor(name=item, function=function),
                    )

                new_model.pk = PkDescriptor(name=new_model.Meta.pkname)
                remove_excluded_parent_fields(new_model)

        return new_model

    @property
    def objects(cls: Type["T"]) -> "QuerySet[T]":  # type: ignore
        if cls.Meta.requires_ref_update:
            raise ModelError(
                f"Model {cls.get_name()} has not updated "
                f"ForwardRefs. \nBefore using the model you "
                f"need to call update_forward_refs()."
            )
        return cls.Meta.queryset_class(model_cls=cls)

    def __getattr__(self, item: str) -> Any:
        """
        Returns FieldAccessors on access to model fields from a class,
        that way it can be used in python style filters and order_by.

        :param item: name of the field
        :type item: str
        :return: FieldAccessor for given field
        :rtype: FieldAccessor
        """
        if item == "pk":
            item = self.Meta.pkname
        if item in object.__getattribute__(self, "Meta").model_fields:
            field = self.Meta.model_fields.get(item)
            if field.is_relation:
                return FieldAccessor(
                    source_model=cast(Type["Model"], self),
                    model=field.to,
                    access_chain=item,
                )
            return FieldAccessor(
                source_model=cast(Type["Model"], self), field=field, access_chain=item
            )
        return object.__getattribute__(self, item)
