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
    Union, cast,
)

from ormar.models.excludable import ExcludableItems
from ormar.models.mixins.relation_mixin import RelationMixin
from ormar.queryset.utils import translate_list_to_dict, update

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model

    T = TypeVar("T", bound=Model)
    IntStr = Union[int, str]
    AbstractSetIntStr = AbstractSet[IntStr]
    MappingIntStrAny = Mapping[IntStr, Any]


class ExcludableMixin(RelationMixin):
    """
    Used to include/exclude given set of fields on models during load and dict() calls.
    """

    if TYPE_CHECKING:  # pragma: no cover
        from ormar import Model
        from ormar.models import ModelRow

    @staticmethod
    def get_child(
            items: Union[Set, Dict, None], key: str = None
    ) -> Union[Set, Dict, None]:
        """
        Used to get nested dictionaries keys if they exists otherwise returns
        passed items.
        :param items: bag of items to include or exclude
        :type items:  Union[Set, Dict, None]
        :param key: name of the child to extract
        :type key: str
        :return: child extracted from items if exists
        :rtype: Union[Set, Dict, None]
        """
        if isinstance(items, dict):
            return items.get(key, {})
        return items

    @staticmethod
    def get_excluded(
            exclude: Union[Set, Dict, None], key: str = None
    ) -> Union[Set, Dict, None]:
        """
        Proxy to ExcludableMixin.get_child for exclusions.

        :param exclude:  bag of items to exclude
        :type exclude: Union[Set, Dict, None]
        :param key: name of the child to extract
        :type key: str
        :return: child extracted from items if exists
        :rtype: Union[Set, Dict, None]
        """
        return ExcludableMixin.get_child(items=exclude, key=key)

    @staticmethod
    def get_included(
            include: Union[Set, Dict, None], key: str = None
    ) -> Union[Set, Dict, None]:
        """
        Proxy to ExcludableMixin.get_child for inclusions.

        :param include:  bag of items to include
        :type include: Union[Set, Dict, None]
        :param key: name of the child to extract
        :type key: str
        :return: child extracted from items if exists
        :rtype: Union[Set, Dict, None]
        """
        return ExcludableMixin.get_child(items=include, key=key)

    @staticmethod
    def is_excluded(exclude: Union[Set, Dict, None], key: str = None) -> bool:
        """
        Checks if given key should be excluded on model/ dict.

        :param exclude:  bag of items to exclude
        :type exclude: Union[Set, Dict, None]
        :param key: name of the child to extract
        :type key: str
        :return: child extracted from items if exists
        :rtype: Union[Set, Dict, None]
        """
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
        """
        Checks if given key should be included on model/ dict.

        :param include:  bag of items to include
        :type include: Union[Set, Dict, None]
        :param key: name of the child to extract
        :type key: str
        :return: child extracted from items if exists
        :rtype: Union[Set, Dict, None]
        """
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
            model: Union[Type["Model"], Type["ModelRow"]],
            columns: List[str],
            use_alias: bool = False,
    ) -> List[str]:
        """
        Adds primary key column/alias (depends on use_alias flag) to list of
        column names that are selected.

        :param model: model on columns are selected
        :type model: Type["Model"]
        :param columns: list of columns names
        :type columns: List[str]
        :param use_alias: flag to set if aliases or field names should be used
        :type use_alias: bool
        :return: list of columns names with pk column in it
        :rtype: List[str]
        """
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
            model: Union[Type["Model"], Type["ModelRow"]],
            excludable: ExcludableItems,
            alias: str = '',
            use_alias: bool = False,
    ) -> List[str]:
        # TODO update docstring
        """
        Returns list of aliases or field names for given model.
        Aliases/names switch is use_alias flag.

        If provided only fields included in fields will be returned.
        If provided fields in exclude_fields will be excluded in return.

        Primary key field is always added and cannot be excluded (will be added anyway).

        :param model: model on columns are selected
        :type model: Type["Model"]
        :param use_alias: flag if aliases or field names should be used
        :type use_alias: bool
        :return: list of column field names or aliases
        :rtype: List[str]
        """
        model_excludable = excludable.get(model_cls=model, alias=alias)
        columns = [
            model.get_column_name_from_alias(col.name) if not use_alias else col.name
            for col in model.Meta.table.columns
        ]
        field_names = [
            model.get_column_name_from_alias(col.name)
            for col in model.Meta.table.columns
        ]
        if model_excludable.include:
            columns = [
                col
                for col, name in zip(columns, field_names)
                if model_excludable.is_included(name)
            ]
        if model_excludable.exclude:
            columns = [
                col
                for col, name in zip(columns, field_names)
                if not model_excludable.is_excluded(name)
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
        """
        Used during generation of the dict().
        To avoid cyclical references and max recurrence limit nested models have to
        exclude related models that are not mandatory.

        For a main model (not nested) only nullable related field names are added to
        exclusion, for nested models all related models are excluded.

        :param exclude: set/dict with fields to exclude
        :type exclude: Union[Set, Dict, None]
        :param nested: flag setting nested models (child of previous one, not main one)
        :type nested: bool
        :return: set or dict with excluded fields added.
        :rtype: Union[Set, Dict]
        """
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
            excludable: ExcludableItems,
            alias: str
    ) -> Set:
        """
        Returns a set of models field names that should be explicitly excluded
        during model initialization.

        Those fields will be set to None to avoid ormar/pydantic setting default
        values on them. They should be returned as None in any case.

        Used in parsing data from database rows that construct Models by initializing
        them with dicts constructed from those db rows.

        :param alias: alias of current relation
        :type alias: str
        :param excludable: structure of fields to include and exclude
        :type excludable: ExcludableItems
        :return: set of field names that should be excluded
        :rtype: Set
        """
        model = cast(Type["Model"], cls)
        model_excludable = excludable.get(model_cls=model, alias=alias)
        fields_names = cls.extract_db_own_fields()
        if model_excludable.include and model_excludable.include_all:
            fields_to_keep = model_excludable.include.intersection(fields_names)
        else:
            fields_to_keep = fields_names

        fields_to_exclude = fields_names - fields_to_keep

        if model_excludable.exclude:
            fields_to_exclude = fields_to_exclude.union(
                model_excludable.exclude.intersection(fields_names)
            )
        fields_to_exclude = fields_to_exclude - {cls.Meta.pkname}

        return fields_to_exclude
