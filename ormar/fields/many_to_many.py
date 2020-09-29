from typing import TYPE_CHECKING, Type

from ormar.fields import BaseField
from ormar.fields.foreign_key import ForeignKeyField

if TYPE_CHECKING:  # pragma no cover
    from ormar.models import Model


def ManyToMany(
    to: Type["Model"],
    through: Type["Model"],
    *,
    name: str = None,
    unique: bool = False,
    related_name: str = None,
    virtual: bool = False,
) -> Type["ManyToManyField"]:
    to_field = to.__fields__[to.Meta.pkname]
    namespace = dict(
        to=to,
        through=through,
        name=name,
        nullable=True,
        unique=unique,
        column_type=to_field.type_.column_type,
        related_name=related_name,
        virtual=virtual,
        primary_key=False,
        index=False,
        pydantic_only=False,
        default=None,
        server_default=None,
    )

    return type("ManyToMany", (ManyToManyField, BaseField), namespace)


class ManyToManyField(ForeignKeyField):
    through: Type["Model"]
