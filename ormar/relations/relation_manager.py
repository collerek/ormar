from typing import List, Optional, TYPE_CHECKING, Type, Union
from weakref import proxy

from ormar.fields.foreign_key import ForeignKeyField
from ormar.fields.many_to_many import ManyToManyField
from ormar.relations.relation import Relation, RelationType
from ormar.relations.utils import (
    get_relations_sides_and_names,
    register_missing_relation,
)

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


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
    def add(parent: "Model", child: "Model", child_name: str, virtual: bool) -> None:
        to_field = child.resolve_relation_field(child, parent)

        (parent, child, child_name, to_name,) = get_relations_sides_and_names(
            to_field, parent, child, child_name, virtual
        )

        parent_relation = parent._orm._get(child_name)
        if not parent_relation:
            parent_relation = register_missing_relation(parent, child, child_name)
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
