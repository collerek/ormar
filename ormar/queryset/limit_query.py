from typing import Optional

import sqlalchemy


class LimitQuery:
    def __init__(self, limit_count: Optional[int]) -> None:
        self.limit_count = limit_count

    def apply(self, expr: sqlalchemy.sql.select) -> sqlalchemy.sql.select:
        if self.limit_count:
            expr = expr.limit(self.limit_count)
        return expr
