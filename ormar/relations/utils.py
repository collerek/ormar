from typing import TYPE_CHECKING, Tuple
from weakref import proxy

from ormar.fields.foreign_key import ForeignKeyField

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


def get_relations_sides_and_names(
    to_field: ForeignKeyField, parent: "Model", child: "Model",
) -> Tuple["Model", "Model", str, str]:
    """
    Determines the names of child and parent relations names, as well as
    changes one of the sides of the relation into weakref.proxy to model.

    :param to_field: field with relation definition
    :type to_field: ForeignKeyField
    :param parent: parent model
    :type parent: Model
    :param child: child model
    :type child: Model
    :return: parent, child, child_name, to_name
    :rtype: Tuple["Model", "Model", str, str]
    """
    to_name = to_field.name
    child_name = to_field.get_related_name()
    if to_field.virtual:
        child_name, to_name = to_name, child_name
        child, parent = parent, proxy(child)
    else:
        child = proxy(child)
    return parent, child, child_name, to_name
