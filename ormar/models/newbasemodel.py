import base64
import sys
import warnings
from typing import (
    AbstractSet,
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    MutableSequence,
    Optional,
    Set,
    TYPE_CHECKING,
    Tuple,
    Type,
    Union,
    cast,
)

try:
    import orjson as json
except ImportError:  # pragma: no cover
    import json  # type: ignore

import databases
import pydantic
import sqlalchemy
from pydantic import BaseModel

import ormar  # noqa I100
from ormar.exceptions import ModelError, ModelPersistenceError
from ormar.fields import BaseField
from ormar.fields.foreign_key import ForeignKeyField
from ormar.models.helpers import register_relation_in_alias_manager
from ormar.models.helpers.relations import expand_reverse_relationship
from ormar.models.helpers.sqlalchemy import (
    populate_meta_sqlalchemy_table_if_required,
    update_column_definition,
)
from ormar.models.metaclass import ModelMeta, ModelMetaclass
from ormar.models.modelproxy import ModelTableProxy
from ormar.queryset.utils import translate_list_to_dict
from ormar.relations.alias_manager import AliasManager
from ormar.relations.relation_manager import RelationsManager

if TYPE_CHECKING:  # pragma no cover
    from ormar.models import Model
    from ormar.signals import SignalEmitter

    IntStr = Union[int, str]
    DictStrAny = Dict[str, Any]
    AbstractSetIntStr = AbstractSet[IntStr]
    MappingIntStrAny = Mapping[IntStr, Any]


class NewBaseModel(pydantic.BaseModel, ModelTableProxy, metaclass=ModelMetaclass):
    """
    Main base class of ormar Model.
    Inherits from pydantic BaseModel and has all mixins combined in ModelTableProxy.
    Constructed with ModelMetaclass which in turn also inherits pydantic metaclass.

    Abstracts away all internals and helper functions, so final Model class has only
    the logic concerned with database connection and data persistance.
    """

    __slots__ = ("_orm_id", "_orm_saved", "_orm", "_pk_column", "__pk_only__")

    if TYPE_CHECKING:  # pragma no cover
        pk: Any
        __model_fields__: Dict[str, BaseField]
        __table__: sqlalchemy.Table
        __fields__: Dict[str, pydantic.fields.ModelField]
        __pydantic_model__: Type[BaseModel]
        __pkname__: str
        __tablename__: str
        __metadata__: sqlalchemy.MetaData
        __database__: databases.Database
        _orm_relationship_manager: AliasManager
        _orm: RelationsManager
        _orm_id: int
        _orm_saved: bool
        _related_names: Optional[Set]
        _through_names: Optional[Set]
        _related_names_hash: str
        _choices_fields: Optional[Set]
        _pydantic_fields: Set
        _quick_access_fields: Set
        _json_fields: Set
        _bytes_fields: Set
        Meta: ModelMeta

    # noinspection PyMissingConstructor
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # type: ignore
        """
        Initializer that creates a new ormar Model that is also pydantic Model at the
        same time.

        Passed keyword arguments can be only field names and their corresponding values
        as those will be passed to pydantic validation that will complain if extra
        params are passed.

        If relations are defined each relation is expanded and children models are also
        initialized and validated. Relation from both sides is registered so you can
        access related models from both sides.

        Json fields are automatically loaded/dumped if needed.

        Models marked as abstract=True in internal Meta class cannot be initialized.

        Accepts also special __pk_only__ flag that indicates that Model is constructed
        only with primary key value (so no other fields, it's a child model on other
        Model), that causes skipping the validation, that's the only case when the
        validation can be skipped.

        Accepts also special __excluded__ parameter that contains a set of fields that
        should be explicitly set to None, as otherwise pydantic will try to populate
        them with their default values if default is set.

        :raises ModelError: if abstract model is initialized, model has ForwardRefs
         that has not been updated or unknown field is passed
        :param args: ignored args
        :type args: Any
        :param kwargs: keyword arguments - all fields values and some special params
        :type kwargs: Any
        """
        self._verify_model_can_be_initialized()
        self._initialize_internal_attributes()

        pk_only = kwargs.pop("__pk_only__", False)
        object.__setattr__(self, "__pk_only__", pk_only)

        new_kwargs, through_tmp_dict = self._process_kwargs(kwargs)

        values, fields_set, validation_error = pydantic.validate_model(
            self, new_kwargs  # type: ignore
        )
        if validation_error and not pk_only:
            raise validation_error

        object.__setattr__(self, "__dict__", values)
        object.__setattr__(self, "__fields_set__", fields_set)

        # add back through fields
        new_kwargs.update(through_tmp_dict)
        model_fields = object.__getattribute__(self, "Meta").model_fields
        # register the columns models after initialization
        for related in self.extract_related_names().union(self.extract_through_names()):
            model_fields[related].expand_relationship(
                new_kwargs.get(related), self, to_register=True,
            )

        if hasattr(self, "_init_private_attributes"):
            # introduced in pydantic 1.7
            self._init_private_attributes()

    def __setattr__(self, name: str, value: Any) -> None:  # noqa CCR001
        """
        Overwrites setattr in pydantic parent as otherwise descriptors are not called.

        :param name: name of the attribute to set
        :type name: str
        :param value: value of the attribute to set
        :type value: Any
        :return: None
        :rtype: None
        """
        if hasattr(self, name):
            object.__setattr__(self, name, value)
        else:
            # let pydantic handle errors for unknown fields
            super().__setattr__(name, value)

    def __getattr__(self, item: str) -> Any:
        """
        Used only to silence mypy errors for Through models and reverse relations.
        Not used in real life as in practice calls are intercepted
        by RelationDescriptors

        :param item: name of attribute
        :type item: str
        :return: Any
        :rtype: Any
        """
        return super().__getattribute__(item)

    def _internal_set(self, name: str, value: Any) -> None:
        """
        Delegates call to pydantic.

        :param name: name of param
        :type name: str
        :param value: value to set
        :type value: Any
        """
        super().__setattr__(name, value)

    def _verify_model_can_be_initialized(self) -> None:
        """
        Raises exception if model is abstract or has ForwardRefs in relation fields.

        :return: None
        :rtype: None
        """
        if self.Meta.abstract:
            raise ModelError(f"You cannot initialize abstract model {self.get_name()}")
        if self.Meta.requires_ref_update:
            raise ModelError(
                f"Model {self.get_name()} has not updated "
                f"ForwardRefs. \nBefore using the model you "
                f"need to call update_forward_refs()."
            )

    def _process_kwargs(self, kwargs: Dict) -> Tuple[Dict, Dict]:
        """
        Initializes nested models.

        Removes property_fields

        Checks if field is in the model fields or pydatnic fields.

        Nullifies fields that should be excluded.

        Extracts through models from kwargs into temporary dict.

        :param kwargs: passed to init keyword arguments
        :type kwargs: Dict
        :return: modified kwargs
        :rtype: Tuple[Dict, Dict]
        """
        property_fields = self.Meta.property_fields
        model_fields = self.Meta.model_fields
        pydantic_fields = set(self.__fields__.keys())

        # remove property fields
        for prop_filed in property_fields:
            kwargs.pop(prop_filed, None)

        excluded: Set[str] = kwargs.pop("__excluded__", set())
        if "pk" in kwargs:
            kwargs[self.Meta.pkname] = kwargs.pop("pk")

        # extract through fields
        through_tmp_dict = dict()
        for field_name in self.extract_through_names():
            through_tmp_dict[field_name] = kwargs.pop(field_name, None)

        try:
            new_kwargs: Dict[str, Any] = {
                k: self._convert_to_bytes(
                    k,
                    self._convert_json(
                        k,
                        model_fields[k].expand_relationship(v, self, to_register=False,)
                        if k in model_fields
                        else (v if k in pydantic_fields else model_fields[k]),
                    ),
                )
                for k, v in kwargs.items()
            }
        except KeyError as e:
            raise ModelError(
                f"Unknown field '{e.args[0]}' for model {self.get_name(lower=False)}"
            )

        # explicitly set None to excluded fields
        # as pydantic populates them with default if set
        for field_to_nullify in excluded:
            new_kwargs[field_to_nullify] = None

        return new_kwargs, through_tmp_dict

    def _initialize_internal_attributes(self) -> None:
        """
        Initializes internal attributes during __init__()
        :rtype: None
        """
        # object.__setattr__(self, "_orm_id", uuid.uuid4().hex)
        object.__setattr__(self, "_orm_saved", False)
        object.__setattr__(self, "_pk_column", None)
        object.__setattr__(
            self,
            "_orm",
            RelationsManager(
                related_fields=self.extract_related_fields(), owner=cast("Model", self),
            ),
        )

    def __eq__(self, other: object) -> bool:
        """
        Compares other model to this model. when == is called.
        :param other: other model to compare
        :type other: object
        :return: result of comparison
        :rtype: bool
        """
        if isinstance(other, NewBaseModel):
            return self.__same__(other)
        return super().__eq__(other)  # pragma no cover

    def __same__(self, other: "NewBaseModel") -> bool:
        """
        Used by __eq__, compares other model to this model.
        Compares:
        * _orm_ids,
        * primary key values if it's set
        * dictionary of own fields (excluding relations)
        :param other: model to compare to
        :type other: NewBaseModel
        :return: result of comparison
        :rtype: bool
        """
        return (
            # self._orm_id == other._orm_id
            (self.pk == other.pk and self.pk is not None)
            or (
                (self.pk is None and other.pk is None)
                and {
                    k: v
                    for k, v in self.__dict__.items()
                    if k not in self.extract_related_names()
                }
                == {
                    k: v
                    for k, v in other.__dict__.items()
                    if k not in other.extract_related_names()
                }
            )
        )

    @classmethod
    def get_name(cls, lower: bool = True) -> str:
        """
        Returns name of the Model class, by default lowercase.

        :param lower: flag if name should be set to lowercase
        :type lower: bool
        :return: name of the model
        :rtype: str
        """
        name = cls.__name__
        if lower:
            name = name.lower()
        return name

    @property
    def pk_column(self) -> sqlalchemy.Column:
        """
        Retrieves primary key sqlalchemy column from models Meta.table.
        Each model has to have primary key.
        Only one primary key column is allowed.

        :return: primary key sqlalchemy column
        :rtype: sqlalchemy.Column
        """
        if object.__getattribute__(self, "_pk_column") is not None:
            return object.__getattribute__(self, "_pk_column")
        pk_columns = self.Meta.table.primary_key.columns.values()
        pk_col = pk_columns[0]
        object.__setattr__(self, "_pk_column", pk_col)
        return pk_col

    @property
    def saved(self) -> bool:
        """Saved status of the model. Changed by setattr and loading from db"""
        return self._orm_saved

    @property
    def signals(self) -> "SignalEmitter":
        """Exposes signals from model Meta"""
        return self.Meta.signals

    @classmethod
    def pk_type(cls) -> Any:
        """Shortcut to models primary key field type"""
        return cls.Meta.model_fields[cls.Meta.pkname].__type__

    @classmethod
    def db_backend_name(cls) -> str:
        """Shortcut to database dialect,
        cause some dialect require different treatment"""
        return cls.Meta.database._backend._dialect.name

    def remove(self, parent: "Model", name: str) -> None:
        """Removes child from relation with given name in RelationshipManager"""
        self._orm.remove_parent(self, parent, name)

    def set_save_status(self, status: bool) -> None:
        """Sets value of the save status"""
        object.__setattr__(self, "_orm_saved", status)

    @classmethod
    def get_properties(
        cls, include: Union[Set, Dict, None], exclude: Union[Set, Dict, None]
    ) -> Set[str]:
        """
        Returns a set of names of functions/fields decorated with
        @property_field decorator.

        They are added to dictionary when called directly and therefore also are
        present in fastapi responses.

        :param include: fields to include
        :type include: Union[Set, Dict, None]
        :param exclude: fields to exclude
        :type exclude: Union[Set, Dict, None]
        :return: set of property fields names
        :rtype: Set[str]
        """

        props = cls.Meta.property_fields
        if include:
            props = {prop for prop in props if prop in include}
        if exclude:
            props = {prop for prop in props if prop not in exclude}
        return props

    @classmethod
    def update_forward_refs(cls, **localns: Any) -> None:
        """
        Processes fields that are ForwardRef and need to be evaluated into actual
        models.

        Expands relationships, register relation in alias manager and substitutes
        sqlalchemy columns with new ones with proper column type (null before).

        Populates Meta table of the Model which is left empty before.

        Sets self_reference flag on models that links to themselves.

        Calls the pydantic method to evaluate pydantic fields.

        :param localns: local namespace
        :type localns: Any
        :return: None
        :rtype: None
        """
        globalns = sys.modules[cls.__module__].__dict__.copy()
        globalns.setdefault(cls.__name__, cls)
        fields_to_check = cls.Meta.model_fields.copy()
        for field in fields_to_check.values():
            if field.has_unresolved_forward_refs():
                field = cast(ForeignKeyField, field)
                field.evaluate_forward_ref(globalns=globalns, localns=localns)
                field.set_self_reference_flag()
                expand_reverse_relationship(model_field=field)
                register_relation_in_alias_manager(field=field)
                update_column_definition(model=cls, field=field)
        populate_meta_sqlalchemy_table_if_required(meta=cls.Meta)
        super().update_forward_refs(**localns)
        cls.Meta.requires_ref_update = False

    def _get_related_not_excluded_fields(
        self, include: Optional[Dict], exclude: Optional[Dict],
    ) -> List:
        """
        Returns related field names applying on them include and exclude set.

        :param include: fields to include
        :type include: Union[Set, Dict, None]
        :param exclude: fields to exclude
        :type exclude: Union[Set, Dict, None]
        :return:
        :rtype: List of fields with relations that is not excluded
        """
        fields = [field for field in self.extract_related_names()]
        if include:
            fields = [field for field in fields if field in include]
        if exclude:
            fields = [
                field
                for field in fields
                if field not in exclude
                or (
                    exclude.get(field) is not Ellipsis
                    and exclude.get(field) != {"__all__"}
                )
            ]
        return fields

    @staticmethod
    def _extract_nested_models_from_list(
        relation_map: Dict,
        models: MutableSequence,
        include: Union[Set, Dict, None],
        exclude: Union[Set, Dict, None],
        exclude_primary_keys: bool,
        exclude_through_models: bool,
    ) -> List:
        """
        Converts list of models into list of dictionaries.

        :param models: List of models
        :type models: List
        :param include: fields to include
        :type include: Union[Set, Dict, None]
        :param exclude: fields to exclude
        :type exclude: Union[Set, Dict, None]
        :return: list of models converted to dictionaries
        :rtype: List[Dict]
        """
        result = []
        for model in models:
            try:
                result.append(
                    model.dict(
                        relation_map=relation_map,
                        include=include,
                        exclude=exclude,
                        exclude_primary_keys=exclude_primary_keys,
                        exclude_through_models=exclude_through_models,
                    )
                )
            except ReferenceError:  # pragma no cover
                continue
        return result

    def _skip_ellipsis(
        self, items: Union[Set, Dict, None], key: str, default_return: Any = None
    ) -> Union[Set, Dict, None]:
        """
        Helper to traverse the include/exclude dictionaries.
        In dict() Ellipsis should be skipped as it indicates all fields required
        and not the actual set/dict with fields names.

        :param items: current include/exclude value
        :type items: Union[Set, Dict, None]
        :param key: key for nested relations to check
        :type key: str
        :return: nested value of the items
        :rtype: Union[Set, Dict, None]
        """
        result = self.get_child(items, key)
        return result if result is not Ellipsis else default_return

    def _convert_all(self, items: Union[Set, Dict, None]) -> Union[Set, Dict, None]:
        """
        Helper to convert __all__ pydantic special index to ormar which does not
        support index based exclusions.

        :param items: current include/exclude value
        :type items: Union[Set, Dict, None]
        """
        if isinstance(items, dict) and "__all__" in items:
            return items.get("__all__")
        return items

    def _extract_nested_models(  # noqa: CCR001
        self,
        relation_map: Dict,
        dict_instance: Dict,
        include: Optional[Dict],
        exclude: Optional[Dict],
        exclude_primary_keys: bool,
        exclude_through_models: bool,
    ) -> Dict:
        """
        Traverse nested models and converts them into dictionaries.
        Calls itself recursively if needed.

        :param nested: flag if current instance is nested
        :type nested: bool
        :param dict_instance: current instance dict
        :type dict_instance: Dict
        :param include: fields to include
        :type include: Optional[Dict]
        :param exclude: fields to exclude
        :type exclude: Optional[Dict]
        :return: current model dict with child models converted to dictionaries
        :rtype: Dict
        """

        fields = self._get_related_not_excluded_fields(include=include, exclude=exclude)

        for field in fields:
            if not relation_map or field not in relation_map:
                continue
            try:
                nested_model = getattr(self, field)
                if isinstance(nested_model, MutableSequence):
                    dict_instance[field] = self._extract_nested_models_from_list(
                        relation_map=self._skip_ellipsis(  # type: ignore
                            relation_map, field, default_return=dict()
                        ),
                        models=nested_model,
                        include=self._convert_all(self._skip_ellipsis(include, field)),
                        exclude=self._convert_all(self._skip_ellipsis(exclude, field)),
                        exclude_primary_keys=exclude_primary_keys,
                        exclude_through_models=exclude_through_models,
                    )
                elif nested_model is not None:

                    dict_instance[field] = nested_model.dict(
                        relation_map=self._skip_ellipsis(
                            relation_map, field, default_return=dict()
                        ),
                        include=self._convert_all(self._skip_ellipsis(include, field)),
                        exclude=self._convert_all(self._skip_ellipsis(exclude, field)),
                        exclude_primary_keys=exclude_primary_keys,
                        exclude_through_models=exclude_through_models,
                    )
                else:
                    dict_instance[field] = None
            except ReferenceError:
                dict_instance[field] = None
        return dict_instance

    def dict(  # type: ignore # noqa A003
        self,
        *,
        include: Union[Set, Dict] = None,
        exclude: Union[Set, Dict] = None,
        by_alias: bool = False,
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        exclude_primary_keys: bool = False,
        exclude_through_models: bool = False,
        relation_map: Dict = None,
    ) -> "DictStrAny":  # noqa: A003'
        """

        Generate a dictionary representation of the model,
        optionally specifying which fields to include or exclude.

        Nested models are also parsed to dictionaries.

        Additionally fields decorated with @property_field are also added.

        :param exclude_through_models: flag to exclude through models from dict
        :type exclude_through_models: bool
        :param exclude_primary_keys: flag to exclude primary keys from dict
        :type exclude_primary_keys: bool
        :param include: fields to include
        :type include: Union[Set, Dict, None]
        :param exclude: fields to exclude
        :type exclude: Union[Set, Dict, None]
        :param by_alias: flag to get values by alias - passed to pydantic
        :type by_alias: bool
        :param skip_defaults: flag to not set values - passed to pydantic
        :type skip_defaults: bool
        :param exclude_unset: flag to exclude not set values - passed to pydantic
        :type exclude_unset: bool
        :param exclude_defaults: flag to exclude default values - passed to pydantic
        :type exclude_defaults: bool
        :param exclude_none: flag to exclude None values - passed to pydantic
        :type exclude_none: bool
        :param relation_map: map of the relations to follow to avoid circural deps
        :type relation_map: Dict
        :return:
        :rtype:
        """
        pydantic_exclude = self._update_excluded_with_related(exclude)
        pydantic_exclude = self._update_excluded_with_pks_and_through(
            exclude=pydantic_exclude,
            exclude_primary_keys=exclude_primary_keys,
            exclude_through_models=exclude_through_models,
        )
        dict_instance = super().dict(
            include=include,
            exclude=pydantic_exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

        dict_instance = {
            k: self._convert_bytes_to_str(column_name=k, value=v)
            for k, v in dict_instance.items()
        }

        if include and isinstance(include, Set):
            include = translate_list_to_dict(include)
        if exclude and isinstance(exclude, Set):
            exclude = translate_list_to_dict(exclude)

        relation_map = (
            relation_map
            if relation_map is not None
            else translate_list_to_dict(self._iterate_related_models())
        )
        pk_only = getattr(self, "__pk_only__", False)
        if relation_map and not pk_only:
            dict_instance = self._extract_nested_models(
                relation_map=relation_map,
                dict_instance=dict_instance,
                include=include,  # type: ignore
                exclude=exclude,  # type: ignore
                exclude_primary_keys=exclude_primary_keys,
                exclude_through_models=exclude_through_models,
            )

        # include model properties as fields in dict
        if object.__getattribute__(self, "Meta").property_fields:
            props = self.get_properties(include=include, exclude=exclude)
            if props:
                dict_instance.update({prop: getattr(self, prop) for prop in props})

        return dict_instance

    def json(  # type: ignore # noqa A003
        self,
        *,
        include: Union[Set, Dict] = None,
        exclude: Union[Set, Dict] = None,
        by_alias: bool = False,
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        encoder: Optional[Callable[[Any], Any]] = None,
        exclude_primary_keys: bool = False,
        exclude_through_models: bool = False,
        **dumps_kwargs: Any,
    ) -> str:
        """
        Generate a JSON representation of the model, `include` and `exclude`
        arguments as per `dict()`.

        `encoder` is an optional function to supply as `default` to json.dumps(),
        other arguments as per `json.dumps()`.
        """
        if skip_defaults is not None:  # pragma: no cover
            warnings.warn(
                f'{self.__class__.__name__}.json(): "skip_defaults" is deprecated '
                f'and replaced by "exclude_unset"',
                DeprecationWarning,
            )
            exclude_unset = skip_defaults
        encoder = cast(Callable[[Any], Any], encoder or self.__json_encoder__)
        data = self.dict(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            exclude_primary_keys=exclude_primary_keys,
            exclude_through_models=exclude_through_models,
        )
        if self.__custom_root_type__:  # pragma: no cover
            data = data["__root__"]
        return self.__config__.json_dumps(data, default=encoder, **dumps_kwargs)

    def update_from_dict(self, value_dict: Dict) -> "NewBaseModel":
        """
        Updates self with values of fields passed in the dictionary.

        :param value_dict: dictionary of fields names and values
        :type value_dict: Dict
        :return: self
        :rtype: NewBaseModel
        """
        for key, value in value_dict.items():
            setattr(self, key, value)
        return self

    def _convert_to_bytes(self, column_name: str, value: Any) -> Union[str, Dict]:
        """
        Converts value to bytes from string

        :param column_name: name of the field
        :type column_name: str
        :param value: value fo the field
        :type value: Any
        :return: converted value if needed, else original value
        :rtype: Any
        """
        if column_name not in self._bytes_fields:
            return value
        field = self.Meta.model_fields[column_name]
        if not isinstance(value, bytes):
            if field.represent_as_base64_str:
                value = base64.b64decode(value)
            else:
                value = value.encode("utf-8")
        return value

    def _convert_bytes_to_str(self, column_name: str, value: Any) -> Union[str, Dict]:
        """
        Converts value to str from bytes for represent_as_base64_str columns.

        :param column_name: name of the field
        :type column_name: str
        :param value: value fo the field
        :type value: Any
        :return: converted value if needed, else original value
        :rtype: Any
        """
        if column_name not in self._bytes_fields:
            return value
        field = self.Meta.model_fields[column_name]
        if not isinstance(value, str) and field.represent_as_base64_str:
            return base64.b64encode(value).decode()
        return value

    def _convert_json(self, column_name: str, value: Any) -> Union[str, Dict]:
        """
        Converts value to/from json if needed (for Json columns).

        :param column_name: name of the field
        :type column_name: str
        :param value: value fo the field
        :type value: Any
        :return: converted value if needed, else original value
        :rtype: Any
        """
        if column_name not in self._json_fields:
            return value
        if not isinstance(value, str):
            try:
                value = json.dumps(value)
            except TypeError:  # pragma no cover
                pass
        return value.decode("utf-8") if isinstance(value, bytes) else value

    def _extract_own_model_fields(self) -> Dict:
        """
        Returns a dictionary with field names and values for fields that are not
        relations fields (ForeignKey, ManyToMany etc.)

        :return: dictionary of fields names and values.
        :rtype: Dict
        """
        related_names = self.extract_related_names()
        self_fields = {k: v for k, v in self.__dict__.items() if k not in related_names}
        return self_fields

    def _extract_model_db_fields(self) -> Dict:
        """
        Returns a dictionary with field names and values for fields that are stored in
        current model's table.

        That includes own non-relational fields ang foreign key fields.

        :return: dictionary of fields names and values.
        :rtype: Dict
        """
        self_fields = self._extract_own_model_fields()
        self_fields = {
            k: v
            for k, v in self_fields.items()
            if self.get_column_alias(k) in self.Meta.table.columns
        }
        for field in self._extract_db_related_names():
            relation_field = self.Meta.model_fields[field]
            target_pk_name = relation_field.to.Meta.pkname
            target_field = getattr(self, field)
            self_fields[field] = getattr(target_field, target_pk_name, None)
            if not relation_field.nullable and not self_fields[field]:
                raise ModelPersistenceError(
                    f"You cannot save {relation_field.to.get_name()} "
                    f"model without pk set!"
                )
        return self_fields

    def get_relation_model_id(self, target_field: "BaseField") -> Optional[int]:
        """
        Returns an id of the relation side model to use in prefetch query.

        :param target_field: field with relation definition
        :type target_field: "BaseField"
        :return: value of pk if set
        :rtype: Optional[int]
        """
        if target_field.virtual or target_field.is_multi:
            return self.pk
        related_name = target_field.name
        related_model = getattr(self, related_name)
        return None if not related_model else related_model.pk
