from enum import Enum
from typing import List, Optional, TYPE_CHECKING, Type, Union

import ormar  # noqa I100
from ormar.exceptions import RelationshipInstanceError  # noqa I100
from ormar.fields.foreign_key import ForeignKeyField  # noqa I100
from ormar.relations.relation_proxy import RelationProxy

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model
    from ormar.relations import RelationsManager


class RelationType(Enum):
    PRIMARY = 1
    REVERSE = 2
    MULTIPLE = 3


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
                if relation_child == child:
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
