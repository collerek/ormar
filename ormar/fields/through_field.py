import sys
from typing import Any, TYPE_CHECKING, Type, Union

from ormar.fields.base import BaseField
from ormar.fields.foreign_key import ForeignKeyField

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model
    from pydantic.typing import ForwardRef

    if sys.version_info < (3, 7):
        ToType = Type[Model]
    else:
        ToType = Union[Type[Model], ForwardRef]


def Through(  # noqa CFQ002
    to: "ToType", *, name: str = None, related_name: str = None, **kwargs: Any,
) -> Any:
    # TODO: clean docstring
    """
    Despite a name it's a function that returns constructed ForeignKeyField.
    This function is actually used in model declaration (as ormar.ForeignKey(ToModel)).

    Accepts number of relation setting parameters as well as all BaseField ones.

    :param to: target related ormar Model
    :type to: Model class
    :param name: name of the database field - later called alias
    :type name: str
    :param related_name: name of reversed FK relation populated for you on to model
    :type related_name: str
    :param virtual: marks if relation is virtual.
    It is for reversed FK and auto generated FK on through model in Many2Many relations.
    :type virtual: bool
    :param kwargs: all other args to be populated by BaseField
    :type kwargs: Any
    :return: ormar ForeignKeyField with relation to selected model
    :rtype: ForeignKeyField
    """

    owner = kwargs.pop("owner", None)
    namespace = dict(
        __type__=to,
        to=to,
        through=None,
        alias=name,
        name=kwargs.pop("real_name", None),
        related_name=related_name,
        virtual=True,
        owner=owner,
        nullable=False,
        unique=False,
        column_type=None,
        primary_key=False,
        index=False,
        pydantic_only=False,
        default=None,
        server_default=None,
        is_relation=True,
        is_through=True,
    )

    return type("Through", (ThroughField, BaseField), namespace)


class ThroughField(ForeignKeyField):
    """
    Field class used to access ManyToMany model through model.
    """
