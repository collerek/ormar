from typing import Dict, TYPE_CHECKING, Type

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
        __pydantic_model__=to,
        # __origin__=List,
        # __args__=[Optional[to]]
    )

    return type("ManyToMany", (ManyToManyField, BaseField), namespace)


class ManyToManyField(ForeignKeyField):
    through: Type["Model"]

    @classmethod
    def __modify_schema__(cls, field_schema: Dict) -> None:
        field_schema["type"] = "array"
        field_schema["title"] = cls.name.title()
        field_schema["definitions"] = {f"{cls.to.__name__}": cls.to.schema()}
        field_schema["items"] = {"$ref": f"{REF_PREFIX}{cls.to.__name__}"}
