from typing import List

import sqlalchemy


class OrderQuery:
    def __init__(self, order_bys: List) -> None:
        self.order_bys = order_bys

    def apply(self, expr: sqlalchemy.sql.select) -> sqlalchemy.sql.select:
        if self.order_bys:
            for order in self.order_bys:
                expr = expr.order_by(order)
        return expr
