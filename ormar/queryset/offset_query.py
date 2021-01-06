from typing import Optional

import sqlalchemy


class OffsetQuery:
    """
    Modifies the select query with offset if set
    """

    def __init__(self, query_offset: Optional[int]) -> None:
        self.query_offset = query_offset

    def apply(self, expr: sqlalchemy.sql.select) -> sqlalchemy.sql.select:
        """
        Applies the offset clause.

        :param expr: query to modify
        :type expr: sqlalchemy.sql.selectable.Select
        :return: modified query
        :rtype: sqlalchemy.sql.selectable.Select
        """
        if self.query_offset:
            expr = expr.offset(self.query_offset)
        return expr
