from typing import Any, List, Optional, TYPE_CHECKING, Type, Union

import ormar
from ormar.fields import BaseField
from ormar.fields.foreign_key import ForeignKeyField

if TYPE_CHECKING:  # pragma no cover
    from ormar.models import Model

REF_PREFIX = "#/components/schemas/"


def ManyToMany(
    to: Type["Model"],
    through: Type["Model"],
    *,
    name: str = None,
    unique: bool = False,
    virtual: bool = False,
    **kwargs: Any
) -> Any:
    to_field = to.Meta.model_fields[to.Meta.pkname]
    related_name = kwargs.pop("related_name", None)
    nullable = kwargs.pop("nullable", True)
    __type__ = (
        Union[to_field.__type__, to, List[to]]  # type: ignore
        if not nullable
        else Optional[Union[to_field.__type__, to, List[to]]]  # type: ignore
    )
    namespace = dict(
        __type__=__type__,
        to=to,
        through=through,
        alias=name,
        name=name,
        nullable=True,
        unique=unique,
        column_type=to_field.column_type,
        related_name=related_name,
        virtual=virtual,
        primary_key=False,
        index=False,
        pydantic_only=False,
        default=None,
        server_default=None,
    )

    return type("ManyToMany", (ManyToManyField, BaseField), namespace)


class ManyToManyField(ForeignKeyField, ormar.QuerySetProtocol, ormar.RelationProtocol):
    through: Type["Model"]
