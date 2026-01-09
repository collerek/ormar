from typing import Optional

import sqlalchemy


class LimitQuery:
    """
    Modifies the select query with limit clause.
    """

    def __init__(self, limit_count: Optional[int]) -> None:
        self.limit_count = limit_count

    def apply(self, expr: sqlalchemy.sql.Select) -> sqlalchemy.sql.Select:
        """
        Applies the limit clause.

        :param expr: query to modify
        :type expr: sqlalchemy.sql.selectable.Select
        :return: modified query
        :rtype: sqlalchemy.sql.selectable.Select
        """

        if self.limit_count is not None:
            expr = expr.limit(self.limit_count)

        return expr
