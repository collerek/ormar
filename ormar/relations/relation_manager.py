from typing import Dict, List, Optional, Sequence, TYPE_CHECKING, Type, TypeVar, Union
from weakref import proxy

from ormar.fields import BaseField
from ormar.fields.foreign_key import ForeignKeyField
from ormar.fields.many_to_many import ManyToManyField
from ormar.relations.relation import Relation, RelationType
from ormar.relations.utils import (
    get_relations_sides_and_names,
    register_missing_relation,
)

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model
    from ormar.models import NewBaseModel

    T = TypeVar("T", bound=Model)


class RelationsManager:
    def __init__(
        self,
        related_fields: List[Type[ForeignKeyField]] = None,
        owner: "NewBaseModel" = None,
    ) -> None:
        self.owner = proxy(owner)
        self._related_fields = related_fields or []
        self._related_names = [field.name for field in self._related_fields]
        self._relations: Dict[str, Relation] = dict()
        for field in self._related_fields:
            self._add_relation(field)

    def _get_relation_type(self, field: Type[BaseField]) -> RelationType:
        if issubclass(field, ManyToManyField):
            return RelationType.MULTIPLE
        return RelationType.PRIMARY if not field.virtual else RelationType.REVERSE

    def _add_relation(self, field: Type[BaseField]) -> None:
        self._relations[field.name] = Relation(
            manager=self,
            type_=self._get_relation_type(field),
            to=field.to,
            through=getattr(field, "through", None),
        )
        if field.name not in self._related_names:
            self._related_names.append(field.name)

    def __contains__(self, item: str) -> bool:
        return item in self._related_names

    def get(self, name: str) -> Optional[Union["T", Sequence["T"]]]:
        relation = self._relations.get(name, None)
        if relation is not None:
            return relation.get()
        return None  # pragma nocover

    def _get(self, name: str) -> Optional[Relation]:
        relation = self._relations.get(name, None)
        if relation is not None:
            return relation
        return None

    @staticmethod
    def add(parent: "Model", child: "Model", child_name: str, virtual: bool) -> None:
        to_field: Type[BaseField] = child.resolve_relation_field(child, parent)

        (parent, child, child_name, to_name,) = get_relations_sides_and_names(
            to_field, parent, child, child_name, virtual
        )

        parent_relation = parent._orm._get(child_name)
        if not parent_relation:
            parent_relation = register_missing_relation(parent, child, child_name)
        parent_relation.add(child)  # type: ignore

        child_relation = child._orm._get(to_name)
        if child_relation:
            child_relation.add(parent)

    def remove(
        self, name: str, child: Union["NewBaseModel", Type["NewBaseModel"]]
    ) -> None:
        relation = self._get(name)
        if relation:
            relation.remove(child)

    @staticmethod
    def remove_parent(
        item: Union["NewBaseModel", Type["NewBaseModel"]], name: "Model"
    ) -> None:
        related_model = name
        rel_name = item.resolve_relation_name(item, related_model)
        if rel_name in item._orm:
            relation_name = item.resolve_relation_name(related_model, item)
            item._orm.remove(rel_name, related_model)
            related_model._orm.remove(relation_name, item)
