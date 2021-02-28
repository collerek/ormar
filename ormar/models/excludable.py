from dataclasses import dataclass, field
from typing import Dict, List, Set, TYPE_CHECKING, Tuple, Type, Union

from ormar.queryset.utils import get_relationship_alias_model_and_str

if TYPE_CHECKING:  # pragma: no cover
    from ormar import Model


@dataclass
class Excludable:
    include: Set = field(default_factory=set)
    exclude: Set = field(default_factory=set)

    @property
    def include_all(self):
        return ... in self.include

    @property
    def exclude_all(self):
        return ... in self.exclude

    def get_copy(self) -> "Excludable":
        _copy = self.__class__()
        _copy.include = {x for x in self.include}
        _copy.exclude = {x for x in self.exclude}
        return _copy

    def set_values(self, value: Set, is_exclude: bool) -> None:
        prop = "exclude" if is_exclude else "include"
        if ... in getattr(self, prop) or ... in value:
            setattr(self, prop, {...})
        else:
            current_value = getattr(self, prop)
            current_value.update(value)
            setattr(self, prop, current_value)

    def is_included(self, key: str) -> bool:
        return (... in self.include or key in self.include) if self.include else True

    def is_excluded(self, key: str) -> bool:
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
        new_excludable = cls()
        for key, value in other.items.items():
            new_excludable.items[key] = value.get_copy()
        return new_excludable

    def get(self, model_cls: Type["Model"], alias: str = "") -> Excludable:
        key = f"{alias + '_' if alias else ''}{model_cls.get_name(lower=True)}"
        return self.items.get(key, Excludable())

    def build(
            self,
            items: Union[List[str], str, Tuple[str], Set[str], Dict],
            model_cls: Type["Model"],
            is_exclude: bool = False,
    ) -> None:

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

        self_fields = set()
        related_items = related_items[:] if related_items else []
        for key, value in values.items():
            if value is ...:
                self_fields.add(key)
            elif isinstance(value, set):
                related_items.append(key)
                (
                    table_prefix,
                    target_model,
                    _,
                    _,
                ) = get_relationship_alias_model_and_str(
                    source_model=source_model, related_parts=related_items
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
