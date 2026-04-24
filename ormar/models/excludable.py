from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, Optional, Union

from ormar.exceptions import QueryDefinitionError
from ormar.queryset.utils import (
    PathParts,
    build_flatten_map,
    get_relationship_alias_model_and_str,
)

if TYPE_CHECKING:  # pragma: no cover
    from ormar import Model


Slot = Literal["include", "exclude", "flatten"]


@dataclass
class Excludable:
    """
    Class that keeps sets of fields to include, exclude, and flatten for a single
    model at a given alias/relation level.
    """

    include: set = field(default_factory=set)
    exclude: set = field(default_factory=set)
    flatten: set = field(default_factory=set)

    def get_copy(self) -> "Excludable":
        """
        Return copy of self to avoid in place modifications.

        :return: copy of self with copied sets
        :rtype: ormar.models.excludable.Excludable
        """
        _copy = self.__class__()
        _copy.include = {x for x in self.include}
        _copy.exclude = {x for x in self.exclude}
        _copy.flatten = {x for x in self.flatten}
        return _copy

    def set_values(self, value: set, slot: Slot) -> None:
        """
        Appends the data to the chosen slot (include/exclude/flatten).

        :param value: set of values to add
        :type value: set
        :param slot: which set to add the values to
        :type slot: Slot
        """
        current_value = getattr(self, slot)
        current_value.update(value)
        setattr(self, slot, current_value)

    def is_included(self, key: str) -> bool:
        """
        Check if field in included (in set or set is {...}).

        :param key: key to check
        :type key: str
        :return: result of the check
        :rtype: bool
        """
        return (... in self.include or key in self.include) if self.include else True

    def is_excluded(self, key: str) -> bool:
        """
        Check if field in excluded (in set or set is {...}).

        :param key: key to check
        :type key: str
        :return: result of the check
        :rtype: bool
        """
        return (... in self.exclude or key in self.exclude) if self.exclude else False

    def is_flattened(self, key: str) -> bool:
        """
        Check if relation is flattened (in set or set is {...}).

        :param key: relation name to check
        :type key: str
        :return: result of the check
        :rtype: bool
        """
        return (... in self.flatten or key in self.flatten) if self.flatten else False


class ExcludableItems:
    """
    Keeps a dictionary of Excludables by alias + model_name keys
    to allow quick lookup by nested models without need to travers
    deeply nested dictionaries and passing include/exclude around.
    """

    def __init__(self) -> None:
        self.items: dict[str, Excludable] = dict()
        self._flatten_paths: set[PathParts] = set()
        self._flatten_map_cache: Optional[dict] = None

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
        new_excludable._flatten_paths = set(other._flatten_paths)
        return new_excludable

    def include_entry_count(self) -> int:
        """
        Returns count of include items inside.
        """
        count = 0
        for key in self.items.keys():
            count += len(self.items[key].include)
        return count

    def has_flatten_entries(self) -> bool:
        """
        Returns whether any Excludable entry has flatten markers.

        :return: True if at least one entry has a non-empty flatten set
        :rtype: bool
        """
        return any(entry.flatten for entry in self.items.values())

    def flatten_map(self) -> Optional[dict]:
        """
        Return a nested-Ellipsis dict representation of the stored flatten
        paths, built lazily on first call and cached for reuse. The cache is
        invalidated whenever ``_set_slot`` adds a new flatten path.

        :return: nested dict keyed by relation names (``...`` at leaves), or
            ``None`` when no flatten paths are stored
        :rtype: Optional[dict]
        """
        if not self._flatten_paths:
            return None
        if self._flatten_map_cache is None:
            self._flatten_map_cache = build_flatten_map(self._flatten_paths)
        return self._flatten_map_cache

    def get(self, model_cls: type["Model"], alias: str = "") -> Excludable:
        """
        Return Excludable for given model and alias.

        :param model_cls: target model to check
        :type model_cls: ormar.models.metaclass.ModelMetaclass
        :param alias: table alias from relation manager
        :type alias: str
        :return: Excludable for given model and alias
        :rtype: ormar.models.excludable.Excludable
        """
        key = _excludable_key(model_cls, alias)
        excludable = self.items.get(key)
        if not excludable:
            excludable = Excludable()
            self.items[key] = excludable
        return excludable

    def build(
        self,
        items: Union[list[str], str, tuple[str], set[str], dict],
        model_cls: type["Model"],
        slot: Slot = "include",
    ) -> None:
        """
        Receives the one of the types of items and parses them as to achieve
        a end situation with one excludable per alias/model in relation.

        Each excludable has three sets of values - include, exclude, and flatten.

        :param items: values to be included, excluded or flattened
        :type items: Union[list[str], str, tuple[str], set[str], dict]
        :param model_cls: source model from which relations are constructed
        :type model_cls: ormar.models.metaclass.ModelMetaclass
        :param slot: which slot to write parsed values into
        :type slot: Slot
        """
        if isinstance(items, str):
            items = {items}

        if isinstance(items, dict):
            self._traverse_dict(
                values=items,
                source_model=model_cls,
                model_cls=model_cls,
                slot=slot,
            )
        else:
            items = set(items)
            nested_items = set(x for x in items if "__" in x)
            items.difference_update(nested_items)
            if items:
                self._set_slot(
                    items=items,
                    model_cls=model_cls,
                    slot=slot,
                )
            if nested_items:
                self._traverse_list(values=nested_items, model_cls=model_cls, slot=slot)

        if slot == "flatten":
            self._validate_flatten_prefix_collisions()

    def _set_slot(
        self,
        items: set,
        model_cls: type["Model"],
        slot: Slot,
        alias: str = "",
        path_parts: PathParts = (),
    ) -> None:
        """
        Sets set of values to be stored for the given slot on the key that
        corresponds to the passed model + alias.

        :param items: items to write
        :type items: set
        :param model_cls: target model on which the items are stored
        :type model_cls: type[Model]
        :param slot: which slot to write to
        :type slot: Slot
        :param alias: table alias from relation manager
        :type alias: str
        :param path_parts: tuple of dunder path segments leading to this model
        :type path_parts: PathParts
        """
        if slot == "flatten":
            self._validate_flatten_leaves(
                items=items, model_cls=model_cls, path_parts=path_parts
            )
            for item in items:
                self._flatten_paths.add(path_parts + (item,))
            self._flatten_map_cache = None

        excludable = self.items.setdefault(
            _excludable_key(model_cls, alias), Excludable()
        )
        excludable.set_values(value=items, slot=slot)

    def _traverse_dict(  # noqa: CFQ002
        self,
        values: dict,
        source_model: type["Model"],
        model_cls: type["Model"],
        slot: Slot,
        path_parts: PathParts = (),
        alias: str = "",
    ) -> None:
        """
        Goes through dict of nested values and construct/update Excludables.

        :param values: items to include/exclude/flatten
        :type values: dict
        :param source_model: source model from which relations are constructed
        :type source_model: ormar.models.metaclass.ModelMetaclass
        :param model_cls: model reached via ``path_parts``
        :type model_cls: ormar.models.metaclass.ModelMetaclass
        :param slot: which slot to write into
        :type slot: Slot
        :param path_parts: tuple of dunder path segments leading to ``model_cls``
        :type path_parts: PathParts
        :param alias: alias of relation
        :type alias: str
        """
        self_fields = set()
        for key, value in values.items():
            if value is ...:
                self_fields.add(key)
            elif isinstance(value, set):
                nested_parts = path_parts + (key,)
                table_prefix, target_model, _, _ = get_relationship_alias_model_and_str(
                    source_model=source_model,
                    related_parts=list(nested_parts),
                )
                self._set_slot(
                    items=value,
                    model_cls=target_model,
                    slot=slot,
                    alias=table_prefix,
                    path_parts=nested_parts,
                )
            else:
                nested_parts = path_parts + (key,)
                table_prefix, target_model, _, _ = get_relationship_alias_model_and_str(
                    source_model=source_model,
                    related_parts=list(nested_parts),
                )
                self._traverse_dict(
                    values=value,
                    source_model=source_model,
                    model_cls=target_model,
                    slot=slot,
                    path_parts=nested_parts,
                    alias=table_prefix,
                )
        if self_fields:
            self._set_slot(
                items=self_fields,
                model_cls=model_cls,
                slot=slot,
                alias=alias,
                path_parts=path_parts,
            )

    def _traverse_list(
        self, values: set[str], model_cls: type["Model"], slot: Slot
    ) -> None:
        """
        Consume a set of dunder-style paths (``"a__b__c"``) and write each leaf
        to the Excludable for its target model/alias. Each path is split once
        into a tuple and threaded through ``_set_slot`` — no further string
        joins happen downstream.

        :param values: set of dunder-style path strings
        :type values: set[str]
        :param model_cls: source model from which relations are resolved
        :type model_cls: type[Model]
        :param slot: which slot to write into
        :type slot: Slot
        """
        for dunder_path in values:
            parts = tuple(dunder_path.split("__"))
            table_prefix, target_model, _, _ = get_relationship_alias_model_and_str(
                source_model=model_cls,
                related_parts=list(parts[:-1]),
            )
            self._set_slot(
                items={parts[-1]},
                model_cls=target_model,
                slot=slot,
                alias=table_prefix,
                path_parts=parts[:-1],
            )

    @staticmethod
    def _validate_flatten_leaves(
        items: set, model_cls: type["Model"], path_parts: PathParts
    ) -> None:
        """
        Ensure every leaf addressed by a flatten spec is a real relation on the
        target model (not a scalar column and not a through model).

        :param items: set of leaf names being flattened on ``model_cls``
        :type items: set
        :param model_cls: target model on which leaves must resolve to relations
        :type model_cls: type[Model]
        :param path_parts: tuple of segments leading to ``model_cls`` (only
            joined for error messages, never parsed)
        :type path_parts: PathParts
        """
        model_fields = model_cls.ormar_config.model_fields
        for item in items:
            related_field = model_fields.get(item)
            if related_field is None:
                raise QueryDefinitionError(
                    f"Unknown relation '{item}' on model "
                    f"{model_cls.get_name(lower=False)} in flatten_fields path "
                    f"'{_join_path(path_parts, item)}'."
                )
            if getattr(related_field, "is_through", False):
                raise QueryDefinitionError(
                    f"Cannot flatten through model '{item}' at path "
                    f"'{_join_path(path_parts, item)}'. Flatten the many-to-many "
                    f"relation itself instead."
                )
            if not getattr(related_field, "is_relation", False):
                raise QueryDefinitionError(
                    f"flatten_fields target '{_join_path(path_parts, item)}' is "
                    f"not a relation on model {model_cls.get_name(lower=False)}. "
                    f"Only foreign keys, many-to-many, and reverse relations can "
                    f"be flattened."
                )

    def _validate_flatten_prefix_collisions(self) -> None:
        """
        Ensure no flatten path is a strict ancestor of another. Flattening a
        relation replaces it with a scalar PK, so a deeper flatten through the
        same chain is unreachable.

        Works directly on tuple paths — sorted so each prefix's descendants
        follow it immediately, enabling an early break once the prefix no
        longer matches.

        :raises QueryDefinitionError: on any prefix collision
        """
        paths = sorted(self._flatten_paths)
        for i, short in enumerate(paths):
            short_len = len(short)
            for longer in paths[i + 1 :]:
                if longer[:short_len] != short:
                    break
                raise QueryDefinitionError(
                    f"Conflicting flatten directives: "
                    f"'{_join_path(short)}' is flattened to its primary key, "
                    f"so nested flatten '{_join_path(longer)}' is unreachable."
                )

    def validate_flatten_vs_excludable(self, source_model: type["Model"]) -> None:
        """
        Ensure no flattened relation has sub-field include/exclude on its target.
        Whole-relation include/exclude at the parent level is allowed; only
        sub-field selection on the flattened child is flagged.

        :param source_model: model from which flatten paths are rooted
        :type source_model: type[Model]
        :raises QueryDefinitionError: when a flattened relation has sub-field
            include/exclude on its target model
        """
        for parts in self._flatten_paths:
            table_prefix, target_model, _, _ = get_relationship_alias_model_and_str(
                source_model=source_model,
                related_parts=list(parts),
            )
            child = self.items.get(_excludable_key(target_model, table_prefix))
            if not child:
                continue
            conflicts = (child.include | child.exclude) - {...}
            if conflicts:
                raise QueryDefinitionError(
                    f"Flatten conflict: relation '{_join_path(parts)}' is "
                    f"flattened but include/exclude specifies children "
                    f"{sorted(conflicts)}. A flattened relation renders only "
                    f"its primary key and cannot have children selected."
                )


def _excludable_key(model_cls: type["Model"], alias: str) -> str:
    """
    Compose the ``{alias}_{model_name}`` key used across ExcludableItems
    lookups. Centralized here so every call site keys entries the same way.

    :param model_cls: target model class
    :type model_cls: type[Model]
    :param alias: table alias from the relation manager (may be empty)
    :type alias: str
    :return: lookup key for ``ExcludableItems.items``
    :rtype: str
    """
    return f"{alias + '_' if alias else ''}{model_cls.get_name(lower=True)}"


def _join_path(parts: PathParts, tail: Optional[str] = None) -> str:
    """
    Build a user-facing dunder path string from a pre-split tuple, optionally
    appending one extra segment. Used only for error messages — the rest of
    the module keeps paths as tuples.

    :param parts: pre-split path segments
    :type parts: PathParts
    :param tail: optional additional segment to append
    :type tail: Optional[str]
    :return: dunder-joined path string
    :rtype: str
    """
    if tail is None:
        return "__".join(parts)
    return "__".join(parts + (tail,)) if parts else tail
