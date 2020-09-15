from enum import Enum
from typing import Any, List, Optional, TYPE_CHECKING, Tuple, Type, Union
from weakref import proxy

import ormar  # noqa I100
from ormar.exceptions import RelationshipInstanceError  # noqa I100
from ormar.fields.foreign_key import ForeignKeyField  # noqa I100
from ormar.fields.many_to_many import ManyToManyField
from ormar.relations.querysetproxy import QuerysetProxy

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


class RelationType(Enum):
    PRIMARY = 1
    REVERSE = 2
    MULTIPLE = 3


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
        if self.relation._type == RelationType.MULTIPLE:
            await self.queryset_proxy.delete_through_instance(item)

    def append(self, item: "Model") -> None:
        super().append(item)

    async def add(self, item: "Model") -> None:
        if self.relation._type == RelationType.MULTIPLE:
            await self.queryset_proxy.create_through_instance(item)
        rel_name = item.resolve_relation_name(item, self._owner)
        setattr(item, rel_name, self._owner)


class Relation:
    def __init__(
        self,
        manager: "RelationsManager",
        type_: RelationType,
        to: Type["Model"],
        through: Type["Model"] = None,
    ) -> None:
        self.manager = manager
        self._owner = manager.owner
        self._type = type_
        self.to = to
        self.through = through
        self.related_models = (
            RelationProxy(relation=self)
            if type_ in (RelationType.REVERSE, RelationType.MULTIPLE)
            else None
        )

    def _find_existing(self, child: "Model") -> Optional[int]:
        for ind, relation_child in enumerate(self.related_models[:]):
            try:
                if relation_child.__same__(child):
                    return ind
            except ReferenceError:  # pragma no cover
                self.related_models.pop(ind)
        return None

    def add(self, child: "Model") -> None:
        relation_name = self._owner.resolve_relation_name(self._owner, child)
        if self._type == RelationType.PRIMARY:
            self.related_models = child
            self._owner.__dict__[relation_name] = child
        else:
            if self._find_existing(child) is None:
                self.related_models.append(child)
                rel = self._owner.__dict__.get(relation_name, [])
                rel = rel or []
                if not isinstance(rel, list):
                    rel = [rel]
                rel.append(child)
                self._owner.__dict__[relation_name] = rel

    def remove(self, child: "Model") -> None:
        relation_name = self._owner.resolve_relation_name(self._owner, child)
        if self._type == RelationType.PRIMARY:
            if self.related_models.__same__(child):
                self.related_models = None
                del self._owner.__dict__[relation_name]
        else:
            position = self._find_existing(child)
            if position is not None:
                self.related_models.pop(position)
                del self._owner.__dict__[relation_name][position]

    def get(self) -> Union[List["Model"], "Model"]:
        return self.related_models

    def __repr__(self) -> str:  # pragma no cover
        return str(self.related_models)


class RelationsManager:
    def __init__(
        self, related_fields: List[Type[ForeignKeyField]] = None, owner: "Model" = None
    ) -> None:
        self.owner = proxy(owner)
        self._related_fields = related_fields or []
        self._related_names = [field.name for field in self._related_fields]
        self._relations = dict()
        for field in self._related_fields:
            self._add_relation(field)

    def _get_relation_type(self, field: Type[ForeignKeyField]) -> RelationType:
        if issubclass(field, ManyToManyField):
            return RelationType.MULTIPLE
        return RelationType.PRIMARY if not field.virtual else RelationType.REVERSE

    def _add_relation(self, field: Type[ForeignKeyField]) -> None:
        self._relations[field.name] = Relation(
            manager=self,
            type_=self._get_relation_type(field),
            to=field.to,
            through=getattr(field, "through", None),
        )

    def __contains__(self, item: str) -> bool:
        return item in self._related_names

    def get(self, name: str) -> Optional[Union[List["Model"], "Model"]]:
        relation = self._relations.get(name, None)
        if relation is not None:
            return relation.get()

    def _get(self, name: str) -> Optional[Relation]:
        relation = self._relations.get(name, None)
        if relation is not None:
            return relation

    @staticmethod
    def register_missing_relation(
        parent: "Model", child: "Model", child_name: str
    ) -> Relation:
        ormar.models.expand_reverse_relationships(child.__class__)
        name = parent.resolve_relation_name(parent, child)
        field = parent.Meta.model_fields[name]
        parent._orm._add_relation(field)
        parent_relation = parent._orm._get(child_name)
        return parent_relation

    @staticmethod
    def get_relations_sides_and_names(
        to_field: Type[ForeignKeyField],
        parent: "Model",
        child: "Model",
        child_name: str,
        virtual: bool,
    ) -> Tuple["Model", "Model", str, str]:
        to_name = to_field.name
        if issubclass(to_field, ManyToManyField):
            child_name, to_name = (
                child.resolve_relation_name(parent, child),
                child.resolve_relation_name(child, parent),
            )
            child = proxy(child)
        elif virtual:
            child_name, to_name = to_name, child_name or child.get_name()
            child, parent = parent, proxy(child)
        else:
            child_name = child_name or child.get_name() + "s"
            child = proxy(child)
        return parent, child, child_name, to_name

    @staticmethod
    def add(parent: "Model", child: "Model", child_name: str, virtual: bool) -> None:
        to_field = next(
            (
                field
                for field in child._orm._related_fields
                if field.to == parent.__class__ or field.to.Meta == parent.Meta
            ),
            None,
        )

        if not to_field:  # pragma no cover
            raise RelationshipInstanceError(
                f"Model {child.__class__} does not have "
                f"reference to model {parent.__class__}"
            )

        (
            parent,
            child,
            child_name,
            to_name,
        ) = RelationsManager.get_relations_sides_and_names(
            to_field, parent, child, child_name, virtual
        )

        parent_relation = parent._orm._get(child_name)
        if not parent_relation:
            parent_relation = RelationsManager.register_missing_relation(
                parent, child, child_name
            )
        parent_relation.add(child)
        child._orm._get(to_name).add(parent)

    def remove(self, name: str, child: "Model") -> None:
        relation = self._get(name)
        relation.remove(child)

    @staticmethod
    def remove_parent(item: "Model", name: Union[str, "Model"]) -> None:
        related_model = name
        name = item.resolve_relation_name(item, related_model)
        if name in item._orm:
            relation_name = item.resolve_relation_name(related_model, item)
            item._orm.remove(name, related_model)
            related_model._orm.remove(relation_name, item)
