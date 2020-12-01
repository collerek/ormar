from typing import (
    Any,
    Dict,
    List,
    MutableSequence,
    Optional,
    Sequence,
    Set,
    TYPE_CHECKING,
    TypeVar,
    Union,
)

import ormar

if TYPE_CHECKING:  # pragma no cover
    from ormar.relations import Relation
    from ormar.models import Model
    from ormar.queryset import QuerySet
    from ormar import RelationType

    T = TypeVar("T", bound=Model)


class QuerysetProxy(ormar.QuerySetProtocol):
    if TYPE_CHECKING:  # pragma no cover
        relation: "Relation"

    def __init__(
        self, relation: "Relation", type_: "RelationType", qryset: "QuerySet" = None
    ) -> None:
        self.relation: Relation = relation
        self._queryset: Optional["QuerySet"] = qryset
        self.type_: "RelationType" = type_
        self._owner: "Model" = self.relation.manager.owner
        self.related_field = self._owner.resolve_relation_field(
            self.relation.to, self._owner
        )
        self.owner_pk_value = self._owner.pk

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
            owner = self._owner
            rel_name = owner.resolve_relation_name(owner, child)
            setattr(owner, rel_name, child)

    def _register_related(self, child: Union["T", Sequence[Optional["T"]]]) -> None:
        if isinstance(child, list):
            for subchild in child:
                self._assign_child_to_parent(subchild)
        else:
            assert isinstance(child, ormar.Model)
            self._assign_child_to_parent(child)

    def _clean_items_on_load(self) -> None:
        if isinstance(self.relation.related_models, MutableSequence):
            for item in self.relation.related_models[:]:
                self.relation.remove(item)

    async def create_through_instance(self, child: "T") -> None:
        queryset = ormar.QuerySet(model_cls=self.relation.through)
        owner_column = self._owner.get_name()
        child_column = child.get_name()
        kwargs = {owner_column: self._owner, child_column: child}
        await queryset.create(**kwargs)

    async def delete_through_instance(self, child: "T") -> None:
        queryset = ormar.QuerySet(model_cls=self.relation.through)
        owner_column = self._owner.get_name()
        child_column = child.get_name()
        kwargs = {owner_column: self._owner, child_column: child}
        link_instance = await queryset.filter(**kwargs).get()  # type: ignore
        await link_instance.delete()

    async def exists(self) -> bool:
        return await self.queryset.exists()

    async def count(self) -> int:
        return await self.queryset.count()

    async def clear(self, keep_reversed: bool = True) -> int:
        if self.type_ == ormar.RelationType.MULTIPLE:
            queryset = ormar.QuerySet(model_cls=self.relation.through)
            owner_column = self._owner.get_name()
        else:
            queryset = ormar.QuerySet(model_cls=self.relation.to)
            owner_column = self.related_field.name
        kwargs = {owner_column: self._owner}
        self._clean_items_on_load()
        if keep_reversed and self.type_ == ormar.RelationType.REVERSE:
            update_kwrgs = {f"{owner_column}": None}
            return await queryset.filter(_exclude=False, **kwargs).update(
                each=False, **update_kwrgs
            )
        return await queryset.delete(**kwargs)  # type: ignore

    async def first(self, **kwargs: Any) -> "Model":
        first = await self.queryset.first(**kwargs)
        self._clean_items_on_load()
        self._register_related(first)
        return first

    async def get(self, **kwargs: Any) -> "Model":
        get = await self.queryset.get(**kwargs)
        self._clean_items_on_load()
        self._register_related(get)
        return get

    async def all(self, **kwargs: Any) -> Sequence[Optional["Model"]]:  # noqa: A003
        all_items = await self.queryset.all(**kwargs)
        self._clean_items_on_load()
        self._register_related(all_items)
        return all_items

    async def create(self, **kwargs: Any) -> "Model":
        if self.type_ == ormar.RelationType.REVERSE:
            kwargs[self.related_field.name] = self._owner
        created = await self.queryset.create(**kwargs)
        self._register_related(created)
        if self.type_ == ormar.RelationType.MULTIPLE:
            await self.create_through_instance(created)
        return created

    async def get_or_create(self, **kwargs: Any) -> "Model":
        try:
            return await self.get(**kwargs)
        except ormar.NoMatch:
            return await self.create(**kwargs)

    async def update_or_create(self, **kwargs: Any) -> "Model":
        pk_name = self.queryset.model_meta.pkname
        if "pk" in kwargs:
            kwargs[pk_name] = kwargs.pop("pk")
        if pk_name not in kwargs or kwargs.get(pk_name) is None:
            return await self.create(**kwargs)
        model = await self.queryset.get(pk=kwargs[pk_name])
        return await model.update(**kwargs)

    def filter(self, **kwargs: Any) -> "QuerysetProxy":  # noqa: A003, A001
        queryset = self.queryset.filter(**kwargs)
        return self.__class__(relation=self.relation, type_=self.type_, qryset=queryset)

    def exclude(self, **kwargs: Any) -> "QuerysetProxy":  # noqa: A003, A001
        queryset = self.queryset.exclude(**kwargs)
        return self.__class__(relation=self.relation, type_=self.type_, qryset=queryset)

    def select_related(self, related: Union[List, str]) -> "QuerysetProxy":
        queryset = self.queryset.select_related(related)
        return self.__class__(relation=self.relation, type_=self.type_, qryset=queryset)

    def prefetch_related(self, related: Union[List, str]) -> "QuerysetProxy":
        queryset = self.queryset.prefetch_related(related)
        return self.__class__(relation=self.relation, type_=self.type_, qryset=queryset)

    def limit(self, limit_count: int) -> "QuerysetProxy":
        queryset = self.queryset.limit(limit_count)
        return self.__class__(relation=self.relation, type_=self.type_, qryset=queryset)

    def offset(self, offset: int) -> "QuerysetProxy":
        queryset = self.queryset.offset(offset)
        return self.__class__(relation=self.relation, type_=self.type_, qryset=queryset)

    def fields(self, columns: Union[List, str, Set, Dict]) -> "QuerysetProxy":
        queryset = self.queryset.fields(columns)
        return self.__class__(relation=self.relation, type_=self.type_, qryset=queryset)

    def exclude_fields(self, columns: Union[List, str, Set, Dict]) -> "QuerysetProxy":
        queryset = self.queryset.exclude_fields(columns=columns)
        return self.__class__(relation=self.relation, type_=self.type_, qryset=queryset)

    def order_by(self, columns: Union[List, str]) -> "QuerysetProxy":
        queryset = self.queryset.order_by(columns)
        return self.__class__(relation=self.relation, type_=self.type_, qryset=queryset)
