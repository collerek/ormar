from typing import (
    AbstractSet,
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Set,
    TYPE_CHECKING,
    Type,
    TypeVar,
    Union,
)

from ormar.models.mixins.relation_mixin import RelationMixin
from ormar.queryset.utils import translate_list_to_dict, update

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model

    T = TypeVar("T", bound=Model)
    IntStr = Union[int, str]
    AbstractSetIntStr = AbstractSet[IntStr]
    MappingIntStrAny = Mapping[IntStr, Any]


class ExcludableMixin(RelationMixin):
    if TYPE_CHECKING:  # pragma: no cover
        from ormar import Model

    @staticmethod
    def get_child(
        items: Union[Set, Dict, None], key: str = None
    ) -> Union[Set, Dict, None]:
        if isinstance(items, dict):
            return items.get(key, {})
        return items

    @staticmethod
    def get_excluded(
        exclude: Union[Set, Dict, None], key: str = None
    ) -> Union[Set, Dict, None]:
        return ExcludableMixin.get_child(items=exclude, key=key)

    @staticmethod
    def get_included(
        include: Union[Set, Dict, None], key: str = None
    ) -> Union[Set, Dict, None]:
        return ExcludableMixin.get_child(items=include, key=key)

    @staticmethod
    def is_excluded(exclude: Union[Set, Dict, None], key: str = None) -> bool:
        if exclude is None:
            return False
        if exclude is Ellipsis:  # pragma: nocover
            return True
        to_exclude = ExcludableMixin.get_excluded(exclude=exclude, key=key)
        if isinstance(to_exclude, Set):
            return key in to_exclude
        if to_exclude is ...:
            return True
        return False

    @staticmethod
    def is_included(include: Union[Set, Dict, None], key: str = None) -> bool:
        if include is None:
            return True
        if include is Ellipsis:
            return True
        to_include = ExcludableMixin.get_included(include=include, key=key)
        if isinstance(to_include, Set):
            return key in to_include
        if to_include is ...:
            return True
        return False

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

    @classmethod
    def own_table_columns(
        cls,
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

        # always has to return pk column for ormar to work
        columns = cls._populate_pk_column(
            model=model, columns=columns, use_alias=use_alias
        )

        return columns

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
