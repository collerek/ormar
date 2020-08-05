from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma no cover
    from orm.models import Model


class RelationshipManager:

    def __init__(self):
        self._relations = dict()

    def add_relation_type(self, relations_key, reverse_key):
        print(relations_key, reverse_key)
        if relations_key not in self._relations:
            self._relations[relations_key] = {'type': 'primary'}
        if reverse_key not in self._relations:
            self._relations[reverse_key] = {'type': 'reverse'}

    def add_relation(self, parent_name: str, child_name: str, parent: 'Model', child: 'Model', virtual: bool = False):
        parent_id = parent._orm_id
        child_id = child._orm_id
        if virtual:
            child_name, parent_name = parent_name, child_name
            child_id, parent_id = parent_id, child_id
            child, parent = parent, child
        self._relations[parent_name.title() + '_' + child_name + 's'].setdefault(parent_id, []).append(
            child)
        self._relations[child_name.title() + '_' + parent_name].setdefault(child_id, []).append(parent)

    def contains(self, relations_key: str, object: 'Model'):
        if relations_key in self._relations:
            return object._orm_id in self._relations[relations_key]
        return False

    def get(self, relations_key: str, object: 'Model'):
        if relations_key in self._relations:
            if object._orm_id in self._relations[relations_key]:
                if self._relations[relations_key]['type'] == 'primary':
                    return self._relations[relations_key][object._orm_id][0]
                return self._relations[relations_key][object._orm_id]

    def __str__(self):  # pragma no cover
        return ''.join(self._relations[rel].__str__() for rel in self._relations)

    def __repr__(self):  # pragma no cover
        return self.__str__()
