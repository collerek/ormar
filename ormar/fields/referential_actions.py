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

    CASCADE: str = "CASCADE"
    RESTRICT: str = "RESTRICT"
    SET_NULL: str = "SET NULL"
    SET_DEFAULT: str = "SET DEFAULT"
    DO_NOTHING: str = "NO ACTION"
