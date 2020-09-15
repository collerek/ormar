from _weakref import proxy
from typing import List, Type, Optional, Union, Tuple

import ormar
from ormar.exceptions import RelationshipInstanceError
from ormar.fields.foreign_key import ForeignKeyField
from ormar.fields.many_to_many import ManyToManyField
from ormar.relations import Relation
from ormar.relations.relation import RelationType


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