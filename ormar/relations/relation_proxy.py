from typing import Any, TYPE_CHECKING

import ormar
from ormar.exceptions import RelationshipInstanceError
from ormar.relations.querysetproxy import QuerysetProxy

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model
    from ormar.relations import Relation
    from ormar.queryset import QuerySet


class RelationProxy(list):
    def __init__(self, relation: "Relation") -> None:
        super(RelationProxy, self).__init__()
        self.relation = relation
        self._owner = self.relation.manager.owner
        self.queryset_proxy = QuerysetProxy(relation=self.relation)

    def __getattribute__(self, item: str) -> Any:
        if item in ["count", "clear"]:
            if not self.queryset_proxy.queryset:
                self.queryset_proxy.queryset = self._set_queryset()
            return getattr(self.queryset_proxy, item)
        return super().__getattribute__(item)

    def __getattr__(self, item: str) -> Any:
        if not self.queryset_proxy.queryset:
            self.queryset_proxy.queryset = self._set_queryset()
        return getattr(self.queryset_proxy, item)

    def _set_queryset(self) -> "QuerySet":
        owner_table = self.relation._owner.Meta.tablename
        pkname = self.relation._owner.Meta.pkname
        pk_value = self.relation._owner.pk
        if not pk_value:
            raise RelationshipInstanceError(
                "You cannot query many to many relationship on unsaved model."
            )
        kwargs = {f"{owner_table}__{pkname}": pk_value}
        queryset = (
            ormar.QuerySet(model_cls=self.relation.to)
            .select_related(owner_table)
            .filter(**kwargs)
        )
        return queryset

    async def remove(self, item: "Model") -> None:
        super().remove(item)
        rel_name = item.resolve_relation_name(item, self._owner)
        item._orm._get(rel_name).remove(self._owner)
        if self.relation._type == ormar.RelationType.MULTIPLE:
            await self.queryset_proxy.delete_through_instance(item)

    def append(self, item: "Model") -> None:
        super().append(item)

    async def add(self, item: "Model") -> None:
        if self.relation._type == ormar.RelationType.MULTIPLE:
            await self.queryset_proxy.create_through_instance(item)
        rel_name = item.resolve_relation_name(item, self._owner)
        setattr(item, rel_name, self._owner)
