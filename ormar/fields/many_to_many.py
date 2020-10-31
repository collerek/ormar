from typing import Any, List, Optional, Sequence, TYPE_CHECKING, Type, Union

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
) -> Type["ManyToManyField"]:
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
        __pydantic_type__=__type__,
        to=to,
        through=through,
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


class ManyToManyField(ForeignKeyField):
    through: Type["Model"]

    if TYPE_CHECKING:  # noqa: C901; pragma nocover

        @staticmethod
        async def add(item: "Model") -> None:
            pass

        @staticmethod
        async def remove(item: "Model") -> None:
            pass

        from ormar import QuerySet

        @staticmethod
        def filter(**kwargs: Any) -> "QuerySet":  # noqa: A003, A001
            pass

        @staticmethod
        def select_related(related: Union[List, str]) -> "QuerySet":
            pass

        @staticmethod
        async def exists() -> bool:
            pass

        @staticmethod
        async def count() -> int:
            pass

        @staticmethod
        async def clear() -> int:
            pass

        @staticmethod
        def limit(limit_count: int) -> "QuerySet":
            pass

        @staticmethod
        def offset(offset: int) -> "QuerySet":
            pass

        @staticmethod
        async def first(**kwargs: Any) -> "Model":
            pass

        @staticmethod
        async def get(**kwargs: Any) -> "Model":
            pass

        @staticmethod
        async def all(**kwargs: Any) -> Sequence[Optional["Model"]]:  # noqa: A003, A001
            pass

        @staticmethod
        async def create(**kwargs: Any) -> "Model":
            pass
