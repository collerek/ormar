"""
Gathers all referential actions by ormar.
"""

from enum import Enum


class ReferentialAction(Enum):
    """
    Because the database management system(DBMS) enforces referential constraints,
    it must ensure data integrity
    if rows in a referenced table are to be deleted (or updated).

    If dependent rows in referencing tables still exist,
    those references have to be considered.

    SQL specifies 5 different referential actions
    that shall take place in such occurrences.
    """

    CASCADE = "CASCADE"
    RESTRICT = "RESTRICT"
    SET_NULL = "SET NULL"
    SET_DEFAULT = "SET DEFAULT"
    DO_NOTHING = "NO ACTION"
