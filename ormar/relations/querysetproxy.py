from typing import Any, List, Optional, Sequence, TYPE_CHECKING, TypeVar, Union

import ormar

if TYPE_CHECKING:  # pragma no cover
    from ormar.relations import Relation
    from ormar.models import Model
    from ormar.queryset import QuerySet

    T = TypeVar("T", bound=Model)


class QuerysetProxy(ormar.QuerySetProtocol):
    if TYPE_CHECKING:  # pragma no cover
        relation: "Relation"

    def __init__(self, relation: "Relation") -> None:
        self.relation: Relation = relation
        self._queryset: Optional["QuerySet"] = None

    @property
    def queryset(self) -> "QuerySet":
        if not self._queryset:
            raise AttributeError
        return self._queryset

    @queryset.setter
    def queryset(self, value: "QuerySet") -> None:
        self._queryset = value

    def _assign_child_to_parent(self, child: Optional["T"]) -> None:
        if child:
            owner = self.relation._owner
            rel_name = owner.resolve_relation_name(owner, child)
            setattr(owner, rel_name, child)

    def _register_related(self, child: Union["T", Sequence[Optional["T"]]]) -> None:
        if isinstance(child, list):
            for subchild in child:
                self._assign_child_to_parent(subchild)
        else:
            assert isinstance(child, ormar.Model)
            self._assign_child_to_parent(child)

    async def create_through_instance(self, child: "T") -> None:
        queryset = ormar.QuerySet(model_cls=self.relation.through)
        owner_column = self.relation._owner.get_name()
        child_column = child.get_name()
        kwargs = {owner_column: self.relation._owner, child_column: child}
        await queryset.create(**kwargs)

    async def delete_through_instance(self, child: "T") -> None:
        queryset = ormar.QuerySet(model_cls=self.relation.through)
        owner_column = self.relation._owner.get_name()
        child_column = child.get_name()
        kwargs = {owner_column: self.relation._owner, child_column: child}
        link_instance = await queryset.filter(**kwargs).get()  # type: ignore
        await link_instance.delete()

    def filter(self, **kwargs: Any) -> "QuerySet":  # noqa: A003
        return self.queryset.filter(**kwargs)

    def select_related(self, related: Union[List, str]) -> "QuerySet":
        return self.queryset.select_related(related)

    async def exists(self) -> bool:
        return await self.queryset.exists()

    async def count(self) -> int:
        return await self.queryset.count()

    async def clear(self) -> int:
        queryset = ormar.QuerySet(model_cls=self.relation.through)
        owner_column = self.relation._owner.get_name()
        kwargs = {owner_column: self.relation._owner}
        return await queryset.delete(**kwargs)  # type: ignore

    def limit(self, limit_count: int) -> "QuerySet":
        return self.queryset.limit(limit_count)

    def offset(self, offset: int) -> "QuerySet":
        return self.queryset.offset(offset)

    async def first(self, **kwargs: Any) -> "Model":
        first = await self.queryset.first(**kwargs)
        self._register_related(first)
        return first

    async def get(self, **kwargs: Any) -> "Model":
        get = await self.queryset.get(**kwargs)
        self._register_related(get)
        return get

    async def all(self, **kwargs: Any) -> Sequence[Optional["Model"]]:  # noqa: A003
        all_items = await self.queryset.all(**kwargs)
        self._register_related(all_items)
        return all_items

    async def create(self, **kwargs: Any) -> "Model":
        create = await self.queryset.create(**kwargs)
        self._register_related(create)
        await self.create_through_instance(create)
        return create
