from typing import List

import sqlalchemy


class FilterQuery:
    def __init__(self, filter_clauses: List, exclude: bool = False) -> None:
        self.exclude = exclude
        self.filter_clauses = filter_clauses

    def apply(self, expr: sqlalchemy.sql.select) -> sqlalchemy.sql.select:
        if self.filter_clauses:
            if len(self.filter_clauses) == 1:
                clause = self.filter_clauses[0]
            else:
                clause = sqlalchemy.sql.and_(*self.filter_clauses)
            clause = sqlalchemy.sql.not_(clause) if self.exclude else clause
            expr = expr.where(clause)
        return expr
