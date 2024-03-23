"""
Package handles relations on models, returning related models on calls and exposing
QuerySetProxy for m2m and reverse relations.
"""

from ormar.relations.alias_manager import AliasManager
from ormar.relations.relation import Relation, RelationType
from ormar.relations.relation_manager import RelationsManager
from ormar.relations.utils import get_relations_sides_and_names

__all__ = [
    "AliasManager",
    "Relation",
    "RelationsManager",
    "RelationType",
    "get_relations_sides_and_names",
]
