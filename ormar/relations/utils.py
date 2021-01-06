from typing import TYPE_CHECKING, Tuple, Type
from weakref import proxy

from ormar.fields import BaseField
from ormar.fields.many_to_many import ManyToManyField

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


def get_relations_sides_and_names(
    to_field: Type[BaseField],
    parent: "Model",
    child: "Model",
    child_name: str,
    virtual: bool,
    relation_name: str,
) -> Tuple["Model", "Model", str, str]:
    """
    Determines the names of child and parent relations names, as well as
    changes one of the sides of the relation into weakref.proxy to model.

    :param to_field: field with relation definition
    :type to_field: BaseField
    :param parent: parent model
    :type parent: Model
    :param child: child model
    :type child: Model
    :param child_name: name of the child
    :type child_name: str
    :param virtual: flag if relation is virtual
    :type virtual: bool
    :param relation_name:
    :type relation_name:
    :return: parent, child, child_name, to_name
    :rtype: Tuple["Model", "Model", str, str]
    """
    to_name = to_field.name
    if issubclass(to_field, ManyToManyField):
        child_name = to_field.related_name or child.get_name() + "s"
        child = proxy(child)
    elif virtual:
        child_name, to_name = to_name, child_name or child.get_name()
        child, parent = parent, proxy(child)
    else:
        child_name = child_name or child.get_name() + "s"
        child = proxy(child)
    return parent, child, child_name, to_name
