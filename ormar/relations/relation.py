from enum import Enum
from typing import (
    Generic,
    List,
    Optional,
    Set,
    TYPE_CHECKING,
    Type,
    TypeVar,
    Union,
    cast,
)

import ormar  # noqa I100
from ormar.exceptions import RelationshipInstanceError  # noqa I100
from ormar.relations.relation_proxy import RelationProxy

if TYPE_CHECKING:  # pragma no cover
    from ormar.relations import RelationsManager
    from ormar.models import Model, NewBaseModel, T
else:
    T = TypeVar("T", bound="Model")


class RelationType(Enum):
    """
    Different types of relations supported by ormar:

    *  ForeignKey = PRIMARY
    *  reverse ForeignKey = REVERSE
    *  ManyToMany = MULTIPLE
    """

    PRIMARY = 1
    REVERSE = 2
    MULTIPLE = 3
    THROUGH = 4


class Relation(Generic[T]):
    """
    Keeps related Models and handles adding/removing of the children.
    """

    def __init__(
        self,
        manager: "RelationsManager",
        type_: RelationType,
        field_name: str,
        to: Type["T"],
        through: Type["Model"] = None,
    ) -> None:
        """
        Initialize the Relation and keep the related models either as instances of
        passed Model, or as a RelationProxy which is basically a list of models with
        some special behavior, as it exposes QuerySetProxy and allows querying the
        related models already pre filtered by parent model.

        :param manager: reference to relation manager
        :type manager: RelationsManager
        :param type_: type of the relation
        :type type_: RelationType
        :param field_name: name of the relation field
        :type field_name: str
        :param to: model to which relation leads to
        :type to: Type[Model]
        :param through: model through which relation goes for m2m relations
        :type through: Type[Model]
        """
        self.manager = manager
        self._owner: "Model" = manager.owner
        self._type: RelationType = type_
        self._to_remove: Set = set()
        self.to: Type["T"] = to
        self._through = through
        self.field_name: str = field_name
        self.related_models: Optional[Union[RelationProxy, "Model"]] = (
            RelationProxy(relation=self, type_=type_, to=to, field_name=field_name)
            if type_ in (RelationType.REVERSE, RelationType.MULTIPLE)
            else None
        )

    def clear(self) -> None:
        if self._type in (RelationType.PRIMARY, RelationType.THROUGH):
            self.related_models = None
            self._owner.__dict__[self.field_name] = None
        elif self.related_models is not None:
            related_models = cast("RelationProxy", self.related_models)
            related_models._clear()
            self._owner.__dict__[self.field_name] = None

    @property
    def through(self) -> Type["Model"]:
        if not self._through:  # pragma: no cover
            raise RelationshipInstanceError("Relation does not have through model!")
        return self._through

    def _clean_related(self) -> None:
        """
        Removes dead weakrefs from RelationProxy.
        """
        cleaned_data = [
            x
            for i, x in enumerate(self.related_models)  # type: ignore
            if i not in self._to_remove
        ]
        self.related_models = RelationProxy(
            relation=self,
            type_=self._type,
            to=self.to,
            field_name=self.field_name,
            data_=cleaned_data,
        )
        relation_name = self.field_name
        self._owner.__dict__[relation_name] = cleaned_data
        self._to_remove = set()

    def _find_existing(
        self, child: Union["NewBaseModel", Type["NewBaseModel"]]
    ) -> Optional[int]:
        """
        Find child model in RelationProxy if exists.

        :param child: child model to find
        :type child: Model
        :return: index of child in RelationProxy
        :rtype: Optional[ind]
        """
        if not isinstance(self.related_models, RelationProxy):  # pragma nocover
            raise ValueError("Cannot find existing models in parent relation type")
        if self._to_remove:
            self._clean_related()
        for ind, relation_child in enumerate(self.related_models[:]):
            try:
                if relation_child == child:
                    return ind
            except ReferenceError:  # pragma no cover
                self._to_remove.add(ind)
        return None

    def add(self, child: "Model") -> None:
        """
        Adds child Model to relation, either sets child as related model or adds
        it to the list in RelationProxy depending on relation type.

        :param child: model to add to relation
        :type child: Model
        """
        relation_name = self.field_name
        if self._type in (RelationType.PRIMARY, RelationType.THROUGH):
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
        """
        Removes child Model from relation, either sets None as related model or removes
        it from the list in RelationProxy depending on relation type.

        :param child: model to remove from relation
        :type child: Model
        """
        relation_name = self.field_name
        if self._type == RelationType.PRIMARY:
            if self.related_models == child:
                self.related_models = None
                del self._owner.__dict__[relation_name]
        else:
            position = self._find_existing(child)
            if position is not None:
                self.related_models.pop(position)  # type: ignore
                del self._owner.__dict__[relation_name][position]

    def get(self) -> Optional[Union[List["Model"], "Model"]]:
        """
        Return the related model or models from RelationProxy.

        :return: related model/models if set
        :rtype: Optional[Union[List[Model], Model]]
        """
        return self.related_models

    def __repr__(self) -> str:  # pragma no cover
        if self._to_remove:
            self._clean_related()
        return str(self.related_models)
