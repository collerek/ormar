from typing import Dict, List, Optional, Sequence, TYPE_CHECKING, Type, TypeVar, Union
from weakref import proxy

from ormar.fields import BaseField
from ormar.fields.foreign_key import ForeignKeyField
from ormar.fields.many_to_many import ManyToManyField
from ormar.relations.relation import Relation, RelationType
from ormar.relations.utils import get_relations_sides_and_names

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
            field_name=field.name,
            to=field.to,
            through=getattr(field, "through", None),
        )

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
    def add(
        parent: "Model",
        child: "Model",
        child_name: str,
        virtual: bool,
        relation_name: str,
    ) -> None:
        to_field: Type[BaseField] = child.Meta.model_fields[relation_name]
        # print('comming', child_name, relation_name)
        (parent, child, child_name, to_name,) = get_relations_sides_and_names(
            to_field, parent, child, child_name, virtual
        )

        # print('adding', parent.get_name(), child.get_name(), child_name)
        parent_relation = parent._orm._get(child_name)
        if parent_relation:
            parent_relation.add(child)  # type: ignore

        # print('adding', child.get_name(), parent.get_name(), child_name)
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
        item: Union["NewBaseModel", Type["NewBaseModel"]], parent: "Model", name: str
    ) -> None:
        relation_name = (
            item.Meta.model_fields[name].related_name or item.get_name() + "s"
        )
        item._orm.remove(name, parent)
        parent._orm.remove(relation_name, item)
