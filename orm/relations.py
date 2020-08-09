import pprint
import string
import uuid
from random import choices
from typing import Dict, List, TYPE_CHECKING, Union
from weakref import proxy

from orm.fields import ForeignKey

if TYPE_CHECKING:  # pragma no cover
    from orm.models import Model


def get_table_alias() -> str:
    return "".join(choices(string.ascii_uppercase, k=2)) + uuid.uuid4().hex[:4]


def get_relation_config(
    relation_type: str, table_name: str, field: ForeignKey
) -> Dict[str, str]:
    alias = get_table_alias()
    config = {
        "type": relation_type,
        "table_alias": alias,
        "source_table": table_name
        if relation_type == "primary"
        else field.to.__tablename__,
        "target_table": field.to.__tablename__
        if relation_type == "primary"
        else table_name,
    }
    return config


class RelationshipManager:
    def __init__(self) -> None:
        self._relations = dict()

    def add_relation_type(
        self, relations_key: str, reverse_key: str, field: ForeignKey, table_name: str
    ) -> None:
        if relations_key not in self._relations:
            self._relations[relations_key] = get_relation_config(
                "primary", table_name, field
            )
        if reverse_key not in self._relations:
            self._relations[reverse_key] = get_relation_config(
                "reverse", table_name, field
            )

    def deregister(self, model: "Model") -> None:
        # print(f'deregistering {model.__class__.__name__}, {model._orm_id}')
        for rel_type in self._relations.keys():
            if model.__class__.__name__.lower() in rel_type.lower():
                if model._orm_id in self._relations[rel_type]:
                    del self._relations[rel_type][model._orm_id]

    def add_relation(
        self,
        parent_name: str,
        child_name: str,
        parent: "Model",
        child: "Model",
        virtual: bool = False,
    ) -> None:
        parent_id = parent._orm_id
        child_id = child._orm_id
        if virtual:
            child_name, parent_name = parent_name, child_name
            child_id, parent_id = parent_id, child_id
            child, parent = parent, proxy(child)
        else:
            child = proxy(child)

        parent_relation_name = parent_name.lower().title() + "_" + child_name + "s"
        parents_list = self._relations[parent_relation_name].setdefault(parent_id, [])
        self.append_related_model(parents_list, child)

        child_relation_name = child_name.lower().title() + "_" + parent_name
        children_list = self._relations[child_relation_name].setdefault(child_id, [])
        self.append_related_model(children_list, parent)

    @staticmethod
    def append_related_model(relations_list: List["Model"], model: "Model") -> None:
        for relation_child in relations_list:
            try:
                if relation_child.__same__(model):
                    return
            except ReferenceError:
                continue

        relations_list.append(model)

    def contains(self, relations_key: str, instance: "Model") -> bool:
        if relations_key in self._relations:
            return instance._orm_id in self._relations[relations_key]
        return False

    def get(
        self, relations_key: str, instance: "Model"
    ) -> Union["Model", List["Model"]]:
        if relations_key in self._relations:
            if instance._orm_id in self._relations[relations_key]:
                if self._relations[relations_key]["type"] == "primary":
                    return self._relations[relations_key][instance._orm_id][0]
                return self._relations[relations_key][instance._orm_id]

    def resolve_relation_join(self, from_table: str, to_table: str) -> str:
        for relation_name, relation in self._relations.items():
            if (
                relation["source_table"] == from_table
                and relation["target_table"] == to_table
            ):
                return self._relations[relation_name]["table_alias"]
        return ""

    def __str__(self) -> str:  # pragma no cover
        return pprint.pformat(self._relations, indent=4, width=1)

    def __repr__(self) -> str:  # pragma no cover
        return self.__str__()
