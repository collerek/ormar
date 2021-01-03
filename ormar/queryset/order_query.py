from typing import Dict

import sqlalchemy


class OrderQuery:
    """
    Modifies the select query with given list of order_by clauses.
    """

    def __init__(self, sorted_orders: Dict) -> None:
        self.sorted_orders = sorted_orders

    def apply(self, expr: sqlalchemy.sql.select) -> sqlalchemy.sql.select:
        """
        Applies all order_by clauses if set.

        :param expr: query to modify
        :type expr: sqlalchemy.sql.selectable.Select
        :return: modified query
        :rtype: sqlalchemy.sql.selectable.Select
        """
        if self.sorted_orders:
            for order in list(self.sorted_orders.values()):
                if order is not None:
                    expr = expr.order_by(order)
        return expr
