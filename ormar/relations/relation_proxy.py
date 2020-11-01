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
        self.relation: Relation = relation
        self._owner: "Model" = self.relation.manager.owner
        self.queryset_proxy = QuerysetProxy(relation=self.relation)

    def __getattribute__(self, item: str) -> Any:
        if item in ["count", "clear"]:
            self._initialize_queryset()
            return getattr(self.queryset_proxy, item)
        return super().__getattribute__(item)

    def __getattr__(self, item: str) -> Any:
        self._initialize_queryset()
        return getattr(self.queryset_proxy, item)

    def _initialize_queryset(self) -> None:
        if not self._check_if_queryset_is_initialized():
            self.queryset_proxy.queryset = self._set_queryset()

    def _check_if_queryset_is_initialized(self) -> bool:
        return (
            hasattr(self.queryset_proxy, "queryset")
            and self.queryset_proxy.queryset is not None
        )

    def _set_queryset(self) -> "QuerySet":
        owner_table = self.relation._owner.Meta.tablename
        pkname = self.relation._owner.get_column_alias(self.relation._owner.Meta.pkname)
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

    async def remove(self, item: "Model") -> None:  # type: ignore
        super().remove(item)
        rel_name = item.resolve_relation_name(item, self._owner)
        relation = item._orm._get(rel_name)
        if relation is None:  # pragma nocover
            raise ValueError(
                f"{self._owner.get_name()} does not have relation {rel_name}"
            )
        relation.remove(self._owner)
        if self.relation._type == ormar.RelationType.MULTIPLE:
            await self.queryset_proxy.delete_through_instance(item)

    def append(self, item: "Model") -> None:
        super().append(item)

    async def add(self, item: "Model") -> None:
        if self.relation._type == ormar.RelationType.MULTIPLE:
            await self.queryset_proxy.create_through_instance(item)
        rel_name = item.resolve_relation_name(item, self._owner)
        if rel_name not in item._orm:  # pragma nocover
            item._orm._add_relation(item.Meta.model_fields[rel_name])
        setattr(item, rel_name, self._owner)
