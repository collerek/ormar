import copy
import sys
import warnings
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)

import pydantic
import sqlalchemy
from pydantic import field_serializer
from pydantic._internal._generics import PydanticGenericMetadata
from pydantic.fields import ComputedFieldInfo, FieldInfo
from pydantic_core.core_schema import SerializerFunctionWrapHandler
from sqlalchemy.sql.schema import ColumnCollectionConstraint

import ormar  # noqa I100
import ormar.fields.constraints
from ormar import ModelDefinitionError  # noqa I100
from ormar.exceptions import ModelError
from ormar.fields import BaseField
from ormar.fields.constraints import CheckColumns, IndexColumns, UniqueColumns
from ormar.fields.foreign_key import ForeignKeyField
from ormar.fields.many_to_many import ManyToManyField
from ormar.models.descriptors import (
    JsonDescriptor,
    PkDescriptor,
    PydanticDescriptor,
    RelationDescriptor,
)
from ormar.models.descriptors.descriptors import BytesDescriptor
from ormar.models.helpers import (
    check_required_config_parameters,
    config_field_not_set,
    expand_reverse_relationships,
    extract_annotations_and_default_vals,
    get_potential_fields,
    merge_or_generate_pydantic_config,
    modify_schema_example,
    populate_config_sqlalchemy_table_if_required,
    populate_config_tablename_columns_and_pk,
    populate_default_options_values,
    register_relation_in_alias_manager,
    remove_excluded_parent_fields,
    sqlalchemy_columns_from_model_fields,
)
from ormar.models.ormar_config import OrmarConfig
from ormar.models.quick_access_views import quick_access_set
from ormar.queryset import FieldAccessor, QuerySet
from ormar.signals import Signal

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model
    from ormar.models import T

CONFIG_KEY = "Config"
PARSED_FIELDS_KEY = "__parsed_fields__"


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
    new_model._json_fields = set()
    new_model._bytes_fields = set()


def add_property_fields(new_model: Type["Model"], attrs: Dict) -> None:  # noqa: CCR001
    """
    Checks class namespace for properties or functions with computed_field.
    If attribute have decorator_info it was decorated with @computed_field.

    Functions like this are exposed in dict() (therefore also fastapi result).
    Names of property fields are cached for quicker access / extraction.

    :param new_model: newly constructed model
    :type new_model: Model class
    :param attrs:
    :type attrs: Dict[str, str]
    """
    props = set()
    for var_name, value in attrs.items():
        if hasattr(value, "decorator_info") and isinstance(
            value.decorator_info, ComputedFieldInfo
        ):
            props.add(var_name)

    if config_field_not_set(model=new_model, field_name="property_fields"):
        new_model.ormar_config.property_fields = props
    else:
        new_model.ormar_config.property_fields = (
            new_model.ormar_config.property_fields.union(props)
        )


def register_signals(new_model: Type["Model"]) -> None:  # noqa: CCR001
    """
    Registers on model's SignalEmmiter and sets pre-defined signals.
    Predefined signals are (pre/post) + (save/update/delete).

    Signals are emitted in both model own methods and in selected queryset ones.

    :param new_model: newly constructed model
    :type new_model: Model class
    """
    if config_field_not_set(model=new_model, field_name="signals"):
        signals = new_model.ormar_config.signals
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
    old_aliases = {
        x.name: x.get_alias() for x in base_class.ormar_config.model_fields.values()
    }
    old_aliases.update(new_aliases)
    constraints_columns = [x._pending_colargs for x in parent_value]
    for column_set in constraints_columns:
        if any(x not in old_aliases.values() for x in column_set):
            raise ModelDefinitionError(
                f"Column constraints "
                f"{column_set} "
                f"has column names "
                f"that are not in the model fields."
                f"\n Check columns redefined in subclasses "
                f"to verify that they have proper 'name' set."
            )


def get_constraint_copy(
    constraint: ColumnCollectionConstraint,
) -> Union[UniqueColumns, IndexColumns, CheckColumns]:
    """
    Copy the constraint and unpacking it's values

    :raises ValueError: if non subclass of ColumnCollectionConstraint
    :param value: an instance of the ColumnCollectionConstraint class
    :type value: Instance of ColumnCollectionConstraint child
    :return: copy ColumnCollectionConstraint ormar constraints
    :rtype: Union[UniqueColumns, IndexColumns, CheckColumns]
    """

    constraints = {
        sqlalchemy.UniqueConstraint: lambda x: UniqueColumns(*x._pending_colargs),
        sqlalchemy.Index: lambda x: IndexColumns(*x._pending_colargs),
        sqlalchemy.CheckConstraint: lambda x: CheckColumns(x.sqltext),
    }
    checks = (key if isinstance(constraint, key) else None for key in constraints)
    target_class = next((target for target in checks if target is not None), None)
    constructor: Optional[Callable] = constraints.get(target_class)
    if not constructor:
        raise ValueError(f"{constraint} must be a ColumnCollectionMixin!")

    return constructor(constraint)


def update_attrs_from_base_config(  # noqa: CCR001
    base_class: "Model", attrs: Dict, model_fields: Dict
) -> None:
    """
    Updates OrmarConfig parameters in child from parent if needed.

    :param base_class: one of the parent classes
    :type base_class: Model or model parent class
    :param attrs: new namespace for class being constructed
    :type attrs: Dict
    :param model_fields: ormar fields in defined in current class
    :type model_fields: Dict[str, BaseField]
    """

    params_to_update = ["metadata", "database", "constraints", "property_fields"]
    for param in params_to_update:
        current_value = attrs.get("ormar_config", {}).__dict__.get(
            param, ormar.Undefined
        )
        parent_value = (
            base_class.ormar_config.__dict__.get(param)
            if hasattr(base_class, "ormar_config")
            else None
        )
        if parent_value:
            if param == "constraints":
                verify_constraint_names(
                    base_class=base_class,
                    model_fields=model_fields,
                    parent_value=parent_value,
                )
                parent_value = [get_constraint_copy(value) for value in parent_value]
            if isinstance(current_value, list):
                current_value.extend(parent_value)
            else:
                setattr(attrs["ormar_config"], param, parent_value)


def copy_and_replace_m2m_through_model(  # noqa: CFQ002
    field: ManyToManyField,
    field_name: str,
    table_name: str,
    parent_fields: Dict,
    attrs: Dict,
    ormar_config: OrmarConfig,
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
    :param ormar_config: metaclass of currently created model
    :type ormar_config: OrmarConfig
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
    new_config = ormar.OrmarConfig(
        tablename=through_class.ormar_config.tablename,
        metadata=through_class.ormar_config.metadata,
        database=through_class.ormar_config.database,
        abstract=through_class.ormar_config.abstract,
        exclude_parent_fields=through_class.ormar_config.exclude_parent_fields,
        queryset_class=through_class.ormar_config.queryset_class,
        extra=through_class.ormar_config.extra,
        constraints=through_class.ormar_config.constraints,
        order_by=through_class.ormar_config.orders_by,
    )
    new_config.table = through_class.ormar_config.pkname
    new_config.pkname = through_class.ormar_config.pkname
    new_config.alias_manager = through_class.ormar_config.alias_manager
    new_config.signals = through_class.ormar_config.signals
    new_config.requires_ref_update = through_class.ormar_config.requires_ref_update
    new_config.model_fields = copy.deepcopy(through_class.ormar_config.model_fields)
    new_config.property_fields = copy.deepcopy(
        through_class.ormar_config.property_fields
    )
    copy_name = through_class.__name__ + attrs.get("__name__", "")
    copy_through = cast(
        Type[ormar.Model], type(copy_name, (ormar.Model,), {"ormar_config": new_config})
    )
    # create new table with copied columns but remove foreign keys
    # they will be populated later in expanding reverse relation
    # if hasattr(new_config, "table"):
    new_config.tablename += "_" + ormar_config.tablename
    new_config.table = None
    new_config.model_fields = {
        name: field
        for name, field in new_config.model_fields.items()
        if not field.is_relation
    }
    _, columns = sqlalchemy_columns_from_model_fields(
        new_config.model_fields, copy_through
    )  # type: ignore
    new_config.columns = columns
    populate_config_sqlalchemy_table_if_required(config=new_config)
    copy_field.through = copy_through

    parent_fields[field_name] = copy_field

    if through_class.ormar_config.table in through_class.ormar_config.metadata:
        through_class.ormar_config.metadata.remove(through_class.ormar_config.table)


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
    if attrs.get("ormar_config"):
        if model_fields and not base_class.ormar_config.abstract:  # type: ignore
            raise ModelDefinitionError(
                f"{curr_class.__name__} cannot inherit "
                f"from non abstract class {base_class.__name__}"
            )
        update_attrs_from_base_config(
            base_class=base_class,  # type: ignore
            attrs=attrs,
            model_fields=model_fields,
        )
        parent_fields: Dict = dict()
        ormar_config = attrs.get("ormar_config")
        if not ormar_config:  # pragma: no cover
            raise ModelDefinitionError(
                f"Model {curr_class.__name__} declared without ormar_config"
            )
        table_name = (
            ormar_config.tablename
            if hasattr(ormar_config, "tablename") and ormar_config.tablename
            else attrs.get("__name__", "").lower() + "s"
        )
        for field_name, field in base_class.ormar_config.model_fields.items():
            if (
                hasattr(ormar_config, "exclude_parent_fields")
                and field_name in ormar_config.exclude_parent_fields
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
                    ormar_config=ormar_config,
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
    if hasattr(base_class, "ormar_config"):
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
    as well as model.ormar_config.model_fields definitions from parents.

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
    elif field.__type__ is bytes:
        setattr(new_model, name, BytesDescriptor(name=name))
    else:
        setattr(new_model, name, PydanticDescriptor(name=name))


def get_serializer() -> Callable:
    def serialize(
        self: "Model",
        value: Optional["Model"],
        handler: SerializerFunctionWrapHandler,
    ) -> Any:
        """
        Serialize a value if it's not expired weak reference.
        """
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore", message="Pydantic serializer warnings"
                )
                return handler(value)
        except ReferenceError:
            return None
        except ValueError as exc:
            if not str(exc).startswith("Circular reference"):
                raise exc
            return {value.ormar_config.pkname: value.pk} if value else None

    return serialize


class ModelMetaclass(pydantic._internal._model_construction.ModelMetaclass):
    def __new__(  # type: ignore # noqa: CCR001
        mcs: "ModelMetaclass",
        name: str,
        bases: Any,
        attrs: dict,
        __pydantic_generic_metadata__: Union[PydanticGenericMetadata, None] = None,
        __pydantic_reset_parent_namespace__: bool = True,
        _create_model_module: Union[str, None] = None,
        **kwargs,
    ) -> type:
        """
        Metaclass used by ormar Models that performs configuration
        and build of ormar Models.


        Sets pydantic configuration.
        Extract model_fields and convert them to pydantic FieldInfo,
        updates class namespace.

        Extracts settings and fields from parent classes.
        Fetches methods decorated with @computed_field decorator
        to expose them later in dict().

        Construct parent pydantic Metaclass/ Model.

        If class has ormar_config declared (so actual ormar Models) it also:

        * populate sqlalchemy columns, pkname and tables from model_fields
        * register reverse relationships on related models
        * registers all relations in alias manager that populates table_prefixes
        * exposes alias manager on each Model
        * creates QuerySet for each model and exposes it on a class
        * sets custom serializers for relation models

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
        if "ormar_config" in attrs:
            attrs["model_config"]["ignored_types"] = (OrmarConfig,)
            attrs["model_config"]["from_attributes"] = True
            for field_name, field in model_fields.items():
                if field.is_relation:
                    decorator = field_serializer(
                        field_name, mode="wrap", check_fields=False
                    )(get_serializer())
                    attrs[f"serialize_{field_name}"] = decorator

        new_model = super().__new__(
            mcs,  # type: ignore
            name,
            bases,
            attrs,
            __pydantic_generic_metadata__=__pydantic_generic_metadata__,
            __pydantic_reset_parent_namespace__=__pydantic_reset_parent_namespace__,
            _create_model_module=_create_model_module,
            **kwargs,
        )

        add_cached_properties(new_model)

        if hasattr(new_model, "ormar_config"):
            populate_default_options_values(new_model, model_fields)
            check_required_config_parameters(new_model)
            add_property_fields(new_model, attrs)
            register_signals(new_model=new_model)
            modify_schema_example(model=new_model)

            if not new_model.ormar_config.abstract:
                new_model = populate_config_tablename_columns_and_pk(name, new_model)
                populate_config_sqlalchemy_table_if_required(new_model.ormar_config)
                expand_reverse_relationships(new_model)
                for field_name, field in new_model.ormar_config.model_fields.items():
                    register_relation_in_alias_manager(field=field)
                    add_field_descriptor(
                        name=field_name, field=field, new_model=new_model
                    )

                if (
                    new_model.ormar_config.pkname
                    and new_model.ormar_config.pkname not in attrs["__annotations__"]
                    and new_model.ormar_config.pkname not in new_model.model_fields
                ):
                    field_name = new_model.ormar_config.pkname
                    new_model.model_fields[field_name] = (
                        FieldInfo.from_annotated_attribute(
                            Optional[int],  # type: ignore
                            None,
                        )
                    )
                    new_model.model_rebuild(force=True)

                new_model.pk = PkDescriptor(name=new_model.ormar_config.pkname)
                remove_excluded_parent_fields(new_model)

        return new_model

    @property
    def objects(cls: Type["T"]) -> "QuerySet[T]":  # type: ignore
        if cls.ormar_config.requires_ref_update:
            raise ModelError(
                f"Model {cls.get_name()} has not updated "
                f"ForwardRefs. \nBefore using the model you "
                f"need to call update_forward_refs()."
            )
        return cls.ormar_config.queryset_class(model_cls=cls)

    def __getattr__(self, item: str) -> Any:
        """
        Returns FieldAccessors on access to model fields from a class,
        that way it can be used in python style filters and order_by.

        :param item: name of the field
        :type item: str
        :return: FieldAccessor for given field
        :rtype: FieldAccessor
        """
        # Ugly workaround for name shadowing warnings in pydantic
        frame = sys._getframe(1)
        file_name = Path(frame.f_code.co_filename)
        if (
            frame.f_code.co_name == "collect_model_fields"
            and file_name.name == "_fields.py"
            and file_name.parent.parent.name == "pydantic"
        ):
            raise AttributeError()
        if item == "pk":
            item = self.ormar_config.pkname
        if item in object.__getattribute__(self, "ormar_config").model_fields:
            field = self.ormar_config.model_fields.get(item)
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
