from enum import Enum
from typing import List, Optional, TYPE_CHECKING, Type, TypeVar, Union

import ormar  # noqa I100
from ormar.exceptions import RelationshipInstanceError  # noqa I100
from ormar.fields.foreign_key import ForeignKeyField  # noqa I100
from ormar.relations.relation_proxy import RelationProxy

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model
    from ormar.relations import RelationsManager
    from ormar.models import NewBaseModel

    T = TypeVar("T", bound=Model)


class RelationType(Enum):
    PRIMARY = 1
    REVERSE = 2
    MULTIPLE = 3


class Relation:
    def __init__(
        self,
        manager: "RelationsManager",
        type_: RelationType,
        to: Type["T"],
        through: Type["T"] = None,
    ) -> None:
        self.manager = manager
        self._owner: "Model" = manager.owner
        self._type: RelationType = type_
        self.to: Type["T"] = to
        self.through: Optional[Type["T"]] = through
        self.related_models: Optional[Union[RelationProxy, "T"]] = (
            RelationProxy(relation=self)
            if type_ in (RelationType.REVERSE, RelationType.MULTIPLE)
            else None
        )

    def _find_existing(
        self, child: Union["NewBaseModel", Type["NewBaseModel"]]
    ) -> Optional[int]:
        if not isinstance(self.related_models, RelationProxy):  # pragma nocover
            raise ValueError("Cannot find existing models in parent relation type")
        for ind, relation_child in enumerate(self.related_models[:]):
            try:
                if relation_child == child:
                    return ind
            except ReferenceError:  # pragma no cover
                self.related_models.pop(ind)
        return None

    def add(self, child: "T") -> None:
        relation_name = self._owner.resolve_relation_name(self._owner, child)
        if self._type == RelationType.PRIMARY:
            self.related_models = child
            self._owner.__dict__[relation_name] = child
        else:
            if self._find_existing(child) is None:
                self.related_models.append(child)  # type: ignore
                rel = self._owner.__dict__.get(relation_name, [])
                rel = rel or []
                if not isinstance(rel, list):
                    rel = [rel]
                rel.append(child)
                self._owner.__dict__[relation_name] = rel

    def remove(self, child: Union["NewBaseModel", Type["NewBaseModel"]]) -> None:
        relation_name = self._owner.resolve_relation_name(self._owner, child)
        if self._type == RelationType.PRIMARY:
            if self.related_models == child:
                self.related_models = None
                del self._owner.__dict__[relation_name]
        else:
            position = self._find_existing(child)
            if position is not None:
                self.related_models.pop(position)  # type: ignore
                del self._owner.__dict__[relation_name][position]

    def get(self) -> Optional[Union[List["T"], "T"]]:
        return self.related_models

    def __repr__(self) -> str:  # pragma no cover
        return str(self.related_models)
