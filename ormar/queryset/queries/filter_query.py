from typing import Any, List, Union

import sqlalchemy
from sqlalchemy import ColumnElement, Select, TextClause

from ormar.queryset.actions.filter_action import FilterAction


class FilterQuery:
    """
    Modifies the select query with given list of where/filter clauses.
    """

    def __init__(
        self, filter_clauses: List[FilterAction], exclude: bool = False
    ) -> None:
        self.exclude = exclude
        self.filter_clauses = filter_clauses

    def apply(
        self,
        expr: Select[Any],
    ) -> Select[Any]:
        """
        Applies all filter clauses if set.

        :param expr: query to modify
        :type expr: sqlalchemy.sql.selectable.Select
        :return: modified query
        :rtype: sqlalchemy.sql.selectable.Select
        """
        if self.filter_clauses:
            if len(self.filter_clauses) == 1:
                clause: Union[TextClause, ColumnElement[Any]] = self.filter_clauses[
                    0
                ].get_text_clause()
            else:
                clause = sqlalchemy.sql.and_(
                    *[x.get_text_clause() for x in self.filter_clauses]
                )
            clause = sqlalchemy.sql.not_(clause) if self.exclude else clause
            expr = expr.where(clause)
        return expr
