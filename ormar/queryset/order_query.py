from typing import Dict

import sqlalchemy


class OrderQuery:
    def __init__(self, sorted_orders: Dict) -> None:
        self.sorted_orders = sorted_orders

    def apply(self, expr: sqlalchemy.sql.select) -> sqlalchemy.sql.select:
        if self.sorted_orders:
            for order in list(self.sorted_orders.values()):
                if order is not None:
                    expr = expr.order_by(order)
        return expr
