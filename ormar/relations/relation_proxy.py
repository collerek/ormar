from typing import Any, Optional, TYPE_CHECKING

import ormar
from ormar.exceptions import NoMatch, RelationshipInstanceError
from ormar.relations.querysetproxy import QuerysetProxy

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model, RelationType
    from ormar.relations import Relation
    from ormar.queryset import QuerySet


class RelationProxy(list):
    def __init__(
        self,
        relation: "Relation",
        type_: "RelationType",
        field_name: str,
        data_: Any = None,
    ) -> None:
        super().__init__(data_ or ())
        self.relation: "Relation" = relation
        self.type_: "RelationType" = type_
        self.field_name = field_name
        self._owner: "Model" = self.relation.manager.owner
        self.queryset_proxy = QuerysetProxy(relation=self.relation, type_=type_)
        self._related_field_name: Optional[str] = None

    @property
    def related_field_name(self) -> str:
        if self._related_field_name:
            return self._related_field_name
        owner_field = self._owner.Meta.model_fields[self.field_name]
        self._related_field_name = (
            owner_field.related_name or self._owner.get_name() + "s"
        )
        return self._related_field_name

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

    def _check_if_model_saved(self) -> None:
        pk_value = self._owner.pk
        if not pk_value:
            raise RelationshipInstanceError(
                "You cannot query relationships from unsaved model."
            )

    def _set_queryset(self) -> "QuerySet":
        related_field_name = self.related_field_name
        related_field = self.relation.to.Meta.model_fields[related_field_name]
        pkname = self._owner.get_column_alias(self._owner.Meta.pkname)
        self._check_if_model_saved()
        kwargs = {f"{related_field.get_alias()}__{pkname}": self._owner.pk}
        queryset = (
            ormar.QuerySet(model_cls=self.relation.to)
            .select_related(related_field.name)
            .filter(**kwargs)
        )
        return queryset

    async def remove(  # type: ignore
        self, item: "Model", keep_reversed: bool = True
    ) -> None:
        if item not in self:
            raise NoMatch(
                f"Object {self._owner.get_name()} has no "
                f"{item.get_name()} with given primary key!"
            )
        super().remove(item)
        relation_name = self.related_field_name
        relation = item._orm._get(relation_name)
        if relation is None:  # pragma nocover
            raise ValueError(
                f"{self._owner.get_name()} does not have relation {relation_name}"
            )
        relation.remove(self._owner)
        self.relation.remove(item)
        if self.type_ == ormar.RelationType.MULTIPLE:
            await self.queryset_proxy.delete_through_instance(item)
        else:
            if keep_reversed:
                setattr(item, relation_name, None)
                await item.update()
            else:
                await item.delete()

    async def add(self, item: "Model") -> None:
        relation_name = self.related_field_name
        if self.type_ == ormar.RelationType.MULTIPLE:
            await self.queryset_proxy.create_through_instance(item)
            setattr(item, relation_name, self._owner)
        else:
            self._check_if_model_saved()
            setattr(item, relation_name, self._owner)
            await item.update()
