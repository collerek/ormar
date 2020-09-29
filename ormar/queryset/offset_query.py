from typing import Optional

import sqlalchemy


class OffsetQuery:
    def __init__(self, query_offset: Optional[int]) -> None:
        self.query_offset = query_offset

    def apply(self, expr: sqlalchemy.sql.select) -> sqlalchemy.sql.select:
        if self.query_offset:
            expr = expr.offset(self.query_offset)
        return expr
