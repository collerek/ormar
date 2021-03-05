from dataclasses import dataclass, field
from typing import Dict, List, Set, TYPE_CHECKING, Tuple, Type, Union

from ormar.queryset.utils import get_relationship_alias_model_and_str

if TYPE_CHECKING:  # pragma: no cover
    from ormar import Model


@dataclass
class Excludable:
    """
    Class that keeps sets of fields to exclude and include
    """

    include: Set = field(default_factory=set)
    exclude: Set = field(default_factory=set)

    def get_copy(self) -> "Excludable":
        """
        Return copy of self to avoid in place modifications
        :return: copy of self with copied sets
        :rtype: ormar.models.excludable.Excludable
        """
        _copy = self.__class__()
        _copy.include = {x for x in self.include}
        _copy.exclude = {x for x in self.exclude}
        return _copy

    def set_values(self, value: Set, is_exclude: bool) -> None:
        """
        Appends the data to include/exclude sets.

        :param value: set of values to add
        :type value: set
        :param is_exclude: flag if values are to be excluded or included
        :type is_exclude: bool
        """
        prop = "exclude" if is_exclude else "include"
        current_value = getattr(self, prop)
        current_value.update(value)
        setattr(self, prop, current_value)

    def is_included(self, key: str) -> bool:
        """
        Check if field in included (in set or set is {...})
        :param key: key to check
        :type key: str
        :return: result of the check
        :rtype: bool
        """
        return (... in self.include or key in self.include) if self.include else True

    def is_excluded(self, key: str) -> bool:
        """
        Check if field in excluded (in set or set is {...})
        :param key: key to check
        :type key: str
        :return: result of the check
        :rtype: bool
        """
        return (... in self.exclude or key in self.exclude) if self.exclude else False


class ExcludableItems:
    """
    Keeps a dictionary of Excludables by alias + model_name keys
    to allow quick lookup by nested models without need to travers
    deeply nested dictionaries and passing include/exclude around
    """

    def __init__(self) -> None:
        self.items: Dict[str, Excludable] = dict()

    @classmethod
    def from_excludable(cls, other: "ExcludableItems") -> "ExcludableItems":
        """
        Copy passed ExcludableItems to avoid inplace modifications.

        :param other: other excludable items to be copied
        :type other: ormar.models.excludable.ExcludableItems
        :return: copy of other
        :rtype: ormar.models.excludable.ExcludableItems
        """
        new_excludable = cls()
        for key, value in other.items.items():
            new_excludable.items[key] = value.get_copy()
        return new_excludable

    def get(self, model_cls: Type["Model"], alias: str = "") -> Excludable:
        """
        Return Excludable for given model and alias.

        :param model_cls: target model to check
        :type model_cls: ormar.models.metaclass.ModelMetaclass
        :param alias: table alias from relation manager
        :type alias: str
        :return: Excludable for given model and alias
        :rtype: ormar.models.excludable.Excludable
        """
        key = f"{alias + '_' if alias else ''}{model_cls.get_name(lower=True)}"
        excludable = self.items.get(key)
        if not excludable:
            excludable = Excludable()
            self.items[key] = excludable
        return excludable

    def build(
        self,
        items: Union[List[str], str, Tuple[str], Set[str], Dict],
        model_cls: Type["Model"],
        is_exclude: bool = False,
    ) -> None:
        """
        Receives the one of the types of items and parses them as to achieve
        a end situation with one excludable per alias/model in relation.

        Each excludable has two sets of values - one to include, one to exclude.

        :param items: values to be included or excluded
        :type items: Union[List[str], str, Tuple[str], Set[str], Dict]
        :param model_cls: source model from which relations are constructed
        :type model_cls: ormar.models.metaclass.ModelMetaclass
        :param is_exclude: flag if items should be included or excluded
        :type is_exclude: bool
        """
        if isinstance(items, str):
            items = {items}

        if isinstance(items, Dict):
            self._traverse_dict(
                values=items,
                source_model=model_cls,
                model_cls=model_cls,
                is_exclude=is_exclude,
            )

        else:
            items = set(items)
            nested_items = set(x for x in items if "__" in x)
            items.difference_update(nested_items)
            self._set_excludes(
                items=items,
                model_name=model_cls.get_name(lower=True),
                is_exclude=is_exclude,
            )
            if nested_items:
                self._traverse_list(
                    values=nested_items, model_cls=model_cls, is_exclude=is_exclude
                )

    def _set_excludes(
        self, items: Set, model_name: str, is_exclude: bool, alias: str = ""
    ) -> None:
        """
        Sets set of values to be included or excluded for given key and model.

        :param items: items to include/exclude
        :type items: set
        :param model_name: name of model to construct key
        :type model_name: str
        :param is_exclude: flag if values should be included or excluded
        :type is_exclude: bool
        :param alias:
        :type alias: str
        """
        key = f"{alias + '_' if alias else ''}{model_name}"
        excludable = self.items.get(key)
        if not excludable:
            excludable = Excludable()
        excludable.set_values(value=items, is_exclude=is_exclude)
        self.items[key] = excludable

    def _traverse_dict(  # noqa: CFQ002
        self,
        values: Dict,
        source_model: Type["Model"],
        model_cls: Type["Model"],
        is_exclude: bool,
        related_items: List = None,
        alias: str = "",
    ) -> None:
        """
        Goes through dict of nested values and construct/update Excludables.

        :param values: items to include/exclude
        :type values: Dict
        :param source_model: source model from which relations are constructed
        :type source_model: ormar.models.metaclass.ModelMetaclass
        :param model_cls: model from which current relation is constructed
        :type model_cls: ormar.models.metaclass.ModelMetaclass
        :param is_exclude: flag if values should be included or excluded
        :type is_exclude: bool
        :param related_items: list of names of related fields chain
        :type related_items: List
        :param alias: alias of relation
        :type alias: str
        """
        self_fields = set()
        related_items = related_items[:] if related_items else []
        for key, value in values.items():
            if value is ...:
                self_fields.add(key)
            elif isinstance(value, set):
                (
                    table_prefix,
                    target_model,
                    _,
                    _,
                ) = get_relationship_alias_model_and_str(
                    source_model=source_model, related_parts=related_items + [key]
                )
                self._set_excludes(
                    items=value,
                    model_name=target_model.get_name(),
                    is_exclude=is_exclude,
                    alias=table_prefix,
                )
            else:
                # dict
                related_items.append(key)
                (
                    table_prefix,
                    target_model,
                    _,
                    _,
                ) = get_relationship_alias_model_and_str(
                    source_model=source_model, related_parts=related_items
                )
                self._traverse_dict(
                    values=value,
                    source_model=source_model,
                    model_cls=target_model,
                    is_exclude=is_exclude,
                    related_items=related_items,
                    alias=table_prefix,
                )
        if self_fields:
            self._set_excludes(
                items=self_fields,
                model_name=model_cls.get_name(),
                is_exclude=is_exclude,
                alias=alias,
            )

    def _traverse_list(
        self, values: Set[str], model_cls: Type["Model"], is_exclude: bool
    ) -> None:
        """
        Goes through list of values and construct/update Excludables.

        :param values: items to include/exclude
        :type values: set
        :param model_cls: model from which current relation is constructed
        :type model_cls: ormar.models.metaclass.ModelMetaclass
        :param is_exclude: flag if values should be included or excluded
        :type is_exclude: bool
        """
        # here we have only nested related keys
        for key in values:
            key_split = key.split("__")
            related_items, field_name = key_split[:-1], key_split[-1]
            (table_prefix, target_model, _, _) = get_relationship_alias_model_and_str(
                source_model=model_cls, related_parts=related_items
            )
            self._set_excludes(
                items={field_name},
                model_name=target_model.get_name(),
                is_exclude=is_exclude,
                alias=table_prefix,
            )
