import string
import string
import uuid
from enum import Enum
from random import choices
from typing import List, TYPE_CHECKING, Type
from weakref import proxy

import sqlalchemy
from sqlalchemy import text

from ormar.exceptions import RelationshipInstanceError
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
        self._relations = dict()
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

    def add_relation_type(
        self,
        relations_key: str,
        reverse_key: str,
        field: ForeignKeyField,
        table_name: str,
    ) -> None:
        if relations_key not in self._relations:
            self._aliases[f"{table_name}_{field.to.Meta.tablename}"] = get_table_alias()
        if reverse_key not in self._relations:
            self._aliases[f"{field.to.Meta.tablename}_{table_name}"] = get_table_alias()

    def resolve_relation_join(self, from_table: str, to_table: str) -> str:
        return self._aliases.get(f"{from_table}_{to_table}", "")


class Relation:
    def __init__(self, type_: RelationType) -> None:
        self._type = type_
        self.related_models = [] if type_ == RelationType.REVERSE else None

    def _find_existing(self, child):
        for ind, relation_child in enumerate(self.related_models):
            try:
                if relation_child.__same__(child):
                    return ind
            except ReferenceError:  # pragma no cover
                continue
        return None

    def add(self, child: "Model") -> None:
        if self._type == RelationType.PRIMARY:
            self.related_models = child
        else:
            if self._find_existing(child) is None:
                self.related_models.append(child)

    # def remove(self, child: "Model") -> None:
    #     if self._type == RelationType.PRIMARY:
    #         self.related_models = None
    #     else:
    #         position = self._find_existing(child)
    #         if position is not None:
    #             self.related_models.pop(position)

    def get(self):
        return self.related_models


class RelationsManager:
    def __init__(
        self, related_fields: List[Type[ForeignKeyField]] = None, owner: "Model" = None
    ):
        self.owner = owner
        self._related_fields = related_fields or []
        self._related_names = [field.name for field in self._related_fields]
        self._relations = dict()
        for field in self._related_fields:
            self._relations[field.name] = Relation(
                type_=RelationType.PRIMARY
                if not field.virtual
                else RelationType.REVERSE
            )

    def __contains__(self, item):
        return item in self._related_names

    def get(self, name):
        relation = self._relations.get(name, None)
        if relation:
            return relation.get()

    def _get(self, name):
        relation = self._relations.get(name, None)
        if relation:
            return relation

    def add(self, parent: "Model", child: "Model", child_name: str, virtual: bool):
        to_field = next(
            (
                field
                for field in child._orm._related_fields
                if field.to == parent.__class__
            ),
            None,
        )

        if not to_field:  # pragma no cover
            raise RelationshipInstanceError(
                f"Model {child.__class__} does not have reference to model {parent.__class__}"
            )

        to_name = to_field.name
        if virtual:
            child_name, to_name = to_name, child_name or child.get_name()
            child, parent = parent, proxy(child)
        else:
            child_name = child_name or child.get_name() + "s"
            child = proxy(child)

        parent._orm._get(child_name).add(child)
        child._orm._get(to_name).add(parent)
