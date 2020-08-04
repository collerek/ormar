from typing import Dict, Union, List

from sqlalchemy import text


class Relationship:

    def __init__(self, name: str, parent: 'Model', child: 'Model', fk_side: str = 'child'):
        self.fk_side = fk_side
        self.child = child
        self.parent = parent
        self.name = name


class RelationshipManager:

    def __init__(self, model: 'Model'):
        self._orm_id: str = model._orm_id
        self._relations: Dict[str, Union[Relationship, List[Relationship]]] = dict()

    def __contains__(self, item):
        return item in self._relations

    def add_related(self, relation: Relationship):
        if relation.fk_side == 'child' and relation.parent._orm_id == self._orm_id:
            new_relation = Relationship(name=relation.parent.__class__.__name__.lower(),
                                        child=relation.parent,
                                        parent=relation.child,
                                        fk_side='parent')
            relation.child._orm_relationship_manager.add(new_relation)

    def add(self, relation: Relationship):
        if relation.name in self._relations:
            self._relations[relation.name].append(relation)
        else:
            self._relations[relation.name] = [relation]
        self.add_related(relation)

    def get(self, name: str):
        for rel, relations in self._relations.items():
            if rel == name:
                if relations and relations[0].fk_side == 'parent':
                    return relations[0].child
                else:
                    return [rela.child for rela in relations]
