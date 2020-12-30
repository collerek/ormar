import inspect
from typing import (
    AbstractSet,
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Set,
    TYPE_CHECKING,
    TypeVar,
    Union,
)

import ormar  # noqa:  I100
from ormar.exceptions import ModelPersistenceError
from ormar.fields import BaseField
from ormar.fields.foreign_key import ForeignKeyField
from ormar.models.metaclass import ModelMeta
from ormar.models.mixins import AliasMixin, MergeModelMixin, PrefetchQueryMixin
from ormar.queryset.utils import translate_list_to_dict, update

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model

    T = TypeVar("T", bound=Model)
    IntStr = Union[int, str]
    AbstractSetIntStr = AbstractSet[IntStr]
    MappingIntStrAny = Mapping[IntStr, Any]

Field = TypeVar("Field", bound=BaseField)


class ModelTableProxy(PrefetchQueryMixin, MergeModelMixin, AliasMixin):
    if TYPE_CHECKING:  # pragma no cover
        Meta: ModelMeta
        _related_names: Optional[Set]
        _related_fields: Optional[List]
        pk: Any
        get_name: Callable
        _props: Set
        dict: Callable  # noqa:  A001, VNE003

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
            if (
                field_name not in new_kwargs
                and field.has_default(use_server=False)
                and not field.pydantic_only
            ):
                new_kwargs[field_name] = field.get_default()
            # clear fields with server_default set as None
            if field.server_default is not None and not new_kwargs.get(field_name):
                new_kwargs.pop(field_name, None)
        return new_kwargs

    @classmethod
    def extract_related_fields(cls) -> List:

        if isinstance(cls._related_fields, List):
            return cls._related_fields

        related_fields = []
        for name in cls.extract_related_names():
            related_fields.append(cls.Meta.model_fields[name])
        cls._related_fields = related_fields

        return related_fields

    @classmethod
    def extract_related_names(cls) -> Set:

        if isinstance(cls._related_names, Set):
            return cls._related_names

        related_names = set()
        for name, field in cls.Meta.model_fields.items():
            if inspect.isclass(field) and issubclass(field, ForeignKeyField):
                related_names.add(name)
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

    @classmethod
    def get_names_to_exclude(
        cls,
        fields: Optional[Union[Dict, Set]] = None,
        exclude_fields: Optional[Union[Dict, Set]] = None,
    ) -> Set:
        fields_names = cls.extract_db_own_fields()
        if fields and fields is not Ellipsis:
            fields_to_keep = {name for name in fields if name in fields_names}
        else:
            fields_to_keep = fields_names

        fields_to_exclude = fields_names - fields_to_keep

        if isinstance(exclude_fields, Set):
            fields_to_exclude = fields_to_exclude.union(
                {name for name in exclude_fields if name in fields_names}
            )
        elif isinstance(exclude_fields, Dict):
            new_to_exclude = {
                name
                for name in exclude_fields
                if name in fields_names and exclude_fields[name] is Ellipsis
            }
            fields_to_exclude = fields_to_exclude.union(new_to_exclude)

        fields_to_exclude = fields_to_exclude - {cls.Meta.pkname}

        return fields_to_exclude
