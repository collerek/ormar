import string
import uuid
from enum import Enum
from random import choices
from typing import List, Optional, TYPE_CHECKING, Type, Union
from weakref import proxy

import sqlalchemy
from sqlalchemy import text

import ormar  # noqa I100
from ormar.exceptions import RelationshipInstanceError  # noqa I100
from ormar.fields.foreign_key import ForeignKeyField  # noqa I100


if TYPE_CHECKING:  # pragma no cover
    from ormar.models import Model


def get_table_alias() -> str:
    return "".join(choices(string.ascii_uppercase, k=2)) + uuid.uuid4().hex[:4]


class RelationType(Enum):
    PRIMARY = 1
    REVERSE = 2


class AliasManager:
    def __init__(self) -> None:
        self._aliases = dict()

    @staticmethod
    def prefixed_columns(alias: str, table: sqlalchemy.Table) -> List[text]:
        return [
            text(f"{alias}_{table.name}.{column.name} as {alias}_{column.name}")
            for column in table.columns
        ]

    @staticmethod
    def prefixed_table_name(alias: str, name: str) -> text:
        return text(f"{name} {alias}_{name}")

    def add_relation_type(self, field: ForeignKeyField, table_name: str,) -> None:
        if f"{table_name}_{field.to.Meta.tablename}" not in self._aliases:
            self._aliases[f"{table_name}_{field.to.Meta.tablename}"] = get_table_alias()
        if f"{field.to.Meta.tablename}_{table_name}" not in self._aliases:
            self._aliases[f"{field.to.Meta.tablename}_{table_name}"] = get_table_alias()

    def resolve_relation_join(self, from_table: str, to_table: str) -> str:
        return self._aliases.get(f"{from_table}_{to_table}", "")


class RelationProxy(list):
    def __init__(self, relation: "Relation") -> None:
        super(RelationProxy, self).__init__()
        self.relation = relation
        self._owner = self.relation.manager.owner

    def remove(self, item: "Model") -> None:
        super().remove(item)
        rel_name = item.resolve_relation_name(item, self._owner)
        item._orm._get(rel_name).remove(self._owner)

    def append(self, item: "Model") -> None:
        super().append(item)

    def add(self, item: "Model") -> None:
        rel_name = item.resolve_relation_name(item, self._owner)
        setattr(item, rel_name, self._owner)


class Relation:
    def __init__(self, manager: "RelationsManager", type_: RelationType) -> None:
        self.manager = manager
        self._owner = manager.owner
        self._type = type_
        self.related_models = (
            RelationProxy(relation=self) if type_ == RelationType.REVERSE else None
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
        self.owner = owner
        self._related_fields = related_fields or []
        self._related_names = [field.name for field in self._related_fields]
        self._relations = dict()
        for field in self._related_fields:
            self._add_relation(field)

    def _add_relation(self, field: Type[ForeignKeyField]) -> None:
        self._relations[field.name] = Relation(
            manager=self,
            type_=RelationType.PRIMARY if not field.virtual else RelationType.REVERSE,
        )

    def __contains__(self, item: str) -> bool:
        return item in self._related_names

    def get(self, name: str) -> Optional[Union[List["Model"], "Model"]]:
        relation = self._relations.get(name, None)
        if relation:
            return relation.get()

    def _get(self, name: str) -> Optional[Relation]:
        relation = self._relations.get(name, None)
        if relation:
            return relation

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

        to_name = to_field.name
        if virtual:
            child_name, to_name = to_name, child_name or child.get_name()
            child, parent = parent, proxy(child)
        else:
            child_name = child_name or child.get_name() + "s"
            child = proxy(child)

        parent_relation = parent._orm._get(child_name)
        if not parent_relation:
            ormar.models.expand_reverse_relationships(child.__class__)
            name = parent.resolve_relation_name(parent, child)
            field = parent.Meta.model_fields[name]
            parent._orm._add_relation(field)
            parent_relation = parent._orm._get(child_name)
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
