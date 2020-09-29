from typing import Optional, TYPE_CHECKING, Tuple, Type
from weakref import proxy

import ormar
from ormar.fields import BaseField
from ormar.fields.many_to_many import ManyToManyField
from ormar.relations import Relation

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


def register_missing_relation(
    parent: "Model", child: "Model", child_name: str
) -> Optional[Relation]:
    ormar.models.expand_reverse_relationships(child.__class__)
    name = parent.resolve_relation_name(parent, child)
    field = parent.Meta.model_fields[name]
    parent._orm._add_relation(field)
    parent_relation = parent._orm._get(child_name)
    return parent_relation


def get_relations_sides_and_names(
    to_field: Type[BaseField],
    parent: "Model",
    child: "Model",
    child_name: str,
    virtual: bool,
) -> Tuple["Model", "Model", str, str]:
    to_name = to_field.name
    if issubclass(to_field, ManyToManyField):
        child_name, to_name = (
            child.resolve_relation_name(parent, child),
            child.resolve_relation_name(child, parent),
        )
        child = proxy(child)
    elif virtual:
        child_name, to_name = to_name, child_name or child.get_name()
        child, parent = parent, proxy(child)
    else:
        child_name = child_name or child.get_name() + "s"
        child = proxy(child)
    return parent, child, child_name, to_name
