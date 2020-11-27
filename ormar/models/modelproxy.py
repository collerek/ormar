import inspect
from collections import OrderedDict
from typing import (
    AbstractSet,
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    TYPE_CHECKING,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from ormar.exceptions import ModelPersistenceError, RelationshipInstanceError
from ormar.queryset.utils import translate_list_to_dict, update

try:
    import orjson as json
except ImportError:  # pragma: nocover
    import json  # type: ignore

import ormar  # noqa:  I100
from ormar.fields import BaseField
from ormar.fields.foreign_key import ForeignKeyField
from ormar.models.metaclass import ModelMeta

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model
    from ormar.models import NewBaseModel

    T = TypeVar("T", bound=Model)
    IntStr = Union[int, str]
    AbstractSetIntStr = AbstractSet[IntStr]
    MappingIntStrAny = Mapping[IntStr, Any]

Field = TypeVar("Field", bound=BaseField)


class ModelTableProxy:
    if TYPE_CHECKING:  # pragma no cover
        Meta: ModelMeta
        _related_names: Set
        _related_names_hash: Union[str, bytes]
        pk: Any
        get_name: Callable

    def dict(self):  # noqa A003
        raise NotImplementedError  # pragma no cover

    def _extract_own_model_fields(self) -> Dict:
        related_names = self.extract_related_names()
        self_fields = {k: v for k, v in self.dict().items() if k not in related_names}
        return self_fields

    @classmethod
    def get_related_field_name(cls, target_field: Type["BaseField"]) -> str:
        if issubclass(target_field, ormar.fields.ManyToManyField):
            return cls.resolve_relation_name(target_field.through, cls)
        if target_field.virtual:
            return cls.resolve_relation_name(target_field.to, cls)
        return target_field.to.Meta.pkname

    @staticmethod
    def get_clause_target_and_filter_column_name(
        parent_model: Type["Model"], target_model: Type["Model"], reverse: bool
    ) -> Tuple[Type["Model"], str]:
        if reverse:
            field = target_model.resolve_relation_field(target_model, parent_model)
            if issubclass(field, ormar.fields.ManyToManyField):
                sub_field = target_model.resolve_relation_field(
                    field.through, parent_model
                )
                return field.through, sub_field.get_alias()
            return target_model, field.get_alias()
        target_field = target_model.get_column_alias(target_model.Meta.pkname)
        return target_model, target_field

    @staticmethod
    def get_column_name_for_id_extraction(
        parent_model: Type["Model"],
        target_model: Type["Model"],
        reverse: bool,
        use_raw: bool,
    ) -> str:
        if reverse:
            column_name = parent_model.Meta.pkname
            return (
                parent_model.get_column_alias(column_name) if use_raw else column_name
            )
        column = target_model.resolve_relation_field(parent_model, target_model)
        return column.get_alias() if use_raw else column.name

    @classmethod
    def get_filtered_names_to_extract(cls, prefetch_dict: Dict) -> List:
        related_to_extract = []
        if prefetch_dict and prefetch_dict is not Ellipsis:
            related_to_extract = [
                related
                for related in cls.extract_related_names()
                if related in prefetch_dict
            ]
        return related_to_extract

    def get_relation_model_id(self, target_field: Type["BaseField"]) -> Optional[int]:
        if target_field.virtual or issubclass(
            target_field, ormar.fields.ManyToManyField
        ):
            return self.pk
        related_name = self.resolve_relation_name(self, target_field.to)
        related_model = getattr(self, related_name)
        return None if not related_model else related_model.pk

    @classmethod
    def extract_db_own_fields(cls) -> Set:
        related_names = cls.extract_related_names()
        self_fields = {
            name for name in cls.Meta.model_fields.keys() if name not in related_names
        }
        return self_fields

    @classmethod
    def substitute_models_with_pks(cls, model_dict: Dict) -> Dict:  # noqa  CCR001
        for field in cls.extract_related_names():
            field_value = model_dict.get(field, None)
            if field_value is not None:
                target_field = cls.Meta.model_fields[field]
                target_pkname = target_field.to.Meta.pkname
                if isinstance(field_value, ormar.Model):
                    pk_value = getattr(field_value, target_pkname)
                    if not pk_value:
                        raise ModelPersistenceError(
                            f"You cannot save {field_value.get_name()} "
                            f"model without pk set!"
                        )
                    model_dict[field] = pk_value
                elif field_value:  # nested dict
                    if isinstance(field_value, list):
                        model_dict[field] = [
                            target.get(target_pkname) for target in field_value
                        ]
                    else:
                        model_dict[field] = field_value.get(target_pkname)
                else:
                    model_dict.pop(field, None)
        return model_dict

    @classmethod
    def populate_default_values(cls, new_kwargs: Dict) -> Dict:
        for field_name, field in cls.Meta.model_fields.items():
            if field_name not in new_kwargs and field.has_default(use_server=False):
                new_kwargs[field_name] = field.get_default()
            # clear fields with server_default set as None
            if field.server_default is not None and not new_kwargs.get(field_name):
                new_kwargs.pop(field_name, None)
        return new_kwargs

    @classmethod
    def get_column_alias(cls, field_name: str) -> str:
        field = cls.Meta.model_fields.get(field_name)
        if field is not None and field.alias is not None:
            return field.alias
        return field_name

    @classmethod
    def get_column_name_from_alias(cls, alias: str) -> str:
        for field_name, field in cls.Meta.model_fields.items():
            if field is not None and field.alias == alias:
                return field_name
        return alias  # if not found it's not an alias but actual name

    @classmethod
    def extract_related_names(cls) -> Set:

        if isinstance(cls._related_names_hash, (str, bytes)):
            return cls._related_names

        related_names = set()
        for name, field in cls.Meta.model_fields.items():
            if inspect.isclass(field) and issubclass(field, ForeignKeyField):
                related_names.add(name)
        cls._related_names_hash = json.dumps(list(cls.Meta.model_fields.keys()))
        cls._related_names = related_names

        return related_names

    @classmethod
    def _extract_db_related_names(cls) -> Set:
        related_names = cls.extract_related_names()
        related_names = {
            name
            for name in related_names
            if cls.Meta.model_fields[name].is_valid_uni_relation()
        }
        return related_names

    @classmethod
    def _exclude_related_names_not_required(cls, nested: bool = False) -> Set:
        if nested:
            return cls.extract_related_names()
        related_names = cls.extract_related_names()
        related_names = {
            name for name in related_names if cls.Meta.model_fields[name].nullable
        }
        return related_names

    @classmethod
    def _update_excluded_with_related_not_required(
        cls,
        exclude: Union["AbstractSetIntStr", "MappingIntStrAny", None],
        nested: bool = False,
    ) -> Union[Set, Dict]:
        exclude = exclude or {}
        related_set = cls._exclude_related_names_not_required(nested=nested)
        if isinstance(exclude, set):
            exclude.union(related_set)
        else:
            related_dict = translate_list_to_dict(related_set)
            exclude = update(related_dict, exclude)
        return exclude

    def _extract_model_db_fields(self) -> Dict:
        self_fields = self._extract_own_model_fields()
        self_fields = {
            k: v
            for k, v in self_fields.items()
            if self.get_column_alias(k) in self.Meta.table.columns
        }
        for field in self._extract_db_related_names():
            target_pk_name = self.Meta.model_fields[field].to.Meta.pkname
            target_field = getattr(self, field)
            self_fields[field] = getattr(target_field, target_pk_name, None)
        return self_fields

    @staticmethod
    def resolve_relation_name(  # noqa CCR001
        item: Union[
            "NewBaseModel",
            Type["NewBaseModel"],
            "ModelTableProxy",
            Type["ModelTableProxy"],
        ],
        related: Union[
            "NewBaseModel",
            Type["NewBaseModel"],
            "ModelTableProxy",
            Type["ModelTableProxy"],
        ],
    ) -> str:
        for name, field in item.Meta.model_fields.items():
            if issubclass(field, ForeignKeyField):
                # fastapi is creating clones of response model
                # that's why it can be a subclass of the original model
                # so we need to compare Meta too as this one is copied as is
                if field.to == related.__class__ or field.to.Meta == related.Meta:
                    return name

        raise ValueError(
            f"No relation between {item.get_name()} and {related.get_name()}"
        )  # pragma nocover

    @staticmethod
    def resolve_relation_field(
        item: Union["Model", Type["Model"]], related: Union["Model", Type["Model"]]
    ) -> Type[BaseField]:
        name = ModelTableProxy.resolve_relation_name(item, related)
        to_field = item.Meta.model_fields.get(name)
        if not to_field:  # pragma no cover
            raise RelationshipInstanceError(
                f"Model {item.__class__} does not have "
                f"reference to model {related.__class__}"
            )
        return to_field

    @classmethod
    def translate_columns_to_aliases(cls, new_kwargs: Dict) -> Dict:
        for field_name, field in cls.Meta.model_fields.items():
            if field_name in new_kwargs:
                new_kwargs[field.get_alias()] = new_kwargs.pop(field_name)
        return new_kwargs

    @classmethod
    def translate_aliases_to_columns(cls, new_kwargs: Dict) -> Dict:
        for field_name, field in cls.Meta.model_fields.items():
            if field.alias and field.alias in new_kwargs:
                new_kwargs[field_name] = new_kwargs.pop(field.alias)
        return new_kwargs

    @classmethod
    def merge_instances_list(cls, result_rows: Sequence["Model"]) -> Sequence["Model"]:
        merged_rows: List["Model"] = []
        grouped_instances: OrderedDict = OrderedDict()

        for model in result_rows:
            grouped_instances.setdefault(model.pk, []).append(model)

        for group in grouped_instances.values():
            model = group.pop(0)
            if group:
                for next_model in group:
                    model = cls.merge_two_instances(next_model, model)
            merged_rows.append(model)

        return merged_rows

    @classmethod
    def merge_two_instances(cls, one: "Model", other: "Model") -> "Model":
        for field in one.Meta.model_fields.keys():
            current_field = getattr(one, field)
            if isinstance(current_field, list) and not isinstance(
                current_field, ormar.Model
            ):
                setattr(other, field, current_field + getattr(other, field))
            elif (
                isinstance(current_field, ormar.Model)
                and current_field.pk == getattr(other, field).pk
            ):
                setattr(
                    other,
                    field,
                    cls.merge_two_instances(current_field, getattr(other, field)),
                )
        other.set_save_status(True)
        return other

    @staticmethod
    def _populate_pk_column(
        model: Type["Model"], columns: List[str], use_alias: bool = False,
    ) -> List[str]:
        pk_alias = (
            model.get_column_alias(model.Meta.pkname)
            if use_alias
            else model.Meta.pkname
        )
        if pk_alias not in columns:
            columns.append(pk_alias)
        return columns

    @staticmethod
    def own_table_columns(
        model: Type["Model"],
        fields: Optional[Union[Set, Dict]],
        exclude_fields: Optional[Union[Set, Dict]],
        use_alias: bool = False,
    ) -> List[str]:
        columns = [
            model.get_column_name_from_alias(col.name) if not use_alias else col.name
            for col in model.Meta.table.columns
        ]
        field_names = [
            model.get_column_name_from_alias(col.name)
            for col in model.Meta.table.columns
        ]
        if fields:
            columns = [
                col
                for col, name in zip(columns, field_names)
                if model.is_included(fields, name)
            ]
        if exclude_fields:
            columns = [
                col
                for col, name in zip(columns, field_names)
                if not model.is_excluded(exclude_fields, name)
            ]

        # always has to return pk column
        columns = ModelTableProxy._populate_pk_column(
            model=model, columns=columns, use_alias=use_alias
        )

        return columns
