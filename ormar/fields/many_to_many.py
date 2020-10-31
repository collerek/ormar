from typing import Any, List, Optional, TYPE_CHECKING, Type, Union, Sequence

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

    if TYPE_CHECKING:  # pragma nocover
        @staticmethod
        async def add(item: "Model") -> None:
            pass

        @staticmethod
        async def remove(item: "Model") -> None:
            pass

        from ormar import QuerySet

        @staticmethod
        def filter(**kwargs: Any) -> "QuerySet":  # noqa: A003
            pass

        @staticmethod
        def select_related(related: Union[List, str]) -> "QuerySet":
            pass

        @staticmethod
        async def exists(self) -> bool:
            return await self.queryset.exists()

        @staticmethod
        async def count(self) -> int:
            return await self.queryset.count()

        @staticmethod
        async def clear(self) -> int:
            pass

        @staticmethod
        def limit(limit_count: int) -> "QuerySet":
            pass

        @staticmethod
        def offset(self, offset: int) -> "QuerySet":
            pass

        @staticmethod
        async def first(self, **kwargs: Any) -> "Model":
            pass

        @staticmethod
        async def get(self, **kwargs: Any) -> "Model":
            pass

        @staticmethod
        async def all(self, **kwargs: Any) -> Sequence[Optional["Model"]]:  # noqa: A003
            pass

        @staticmethod
        async def create(self, **kwargs: Any) -> "Model":
            pass
