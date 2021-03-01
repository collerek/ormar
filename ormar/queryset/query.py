from collections import OrderedDict
from typing import List, Optional, TYPE_CHECKING, Tuple, Type

import sqlalchemy
from sqlalchemy import text

import ormar  # noqa I100
from ormar.models.helpers.models import group_related_list
from ormar.queryset import FilterQuery, LimitQuery, OffsetQuery, OrderQuery
from ormar.queryset.actions.filter_action import FilterAction
from ormar.queryset.join import SqlJoin

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model
    from ormar.queryset import OrderAction
    from ormar.models.excludable import ExcludableItems


class Query:
    def __init__(  # noqa CFQ002
        self,
        model_cls: Type["Model"],
        filter_clauses: List[FilterAction],
        exclude_clauses: List[FilterAction],
        select_related: List,
        limit_count: Optional[int],
        offset: Optional[int],
        excludable: "ExcludableItems",
        order_bys: Optional[List["OrderAction"]],
        limit_raw_sql: bool,
    ) -> None:
        self.query_offset = offset
        self.limit_count = limit_count
        self._select_related = select_related[:]
        self.filter_clauses = filter_clauses[:]
        self.exclude_clauses = exclude_clauses[:]
        self.excludable = excludable

        self.model_cls = model_cls
        self.table = self.model_cls.Meta.table

        self.used_aliases: List[str] = []

        self.select_from: List[str] = []
        self.columns = [sqlalchemy.Column]
        self.order_columns = order_bys
        self.sorted_orders: OrderedDict[OrderAction, text] = OrderedDict()
        self._init_sorted_orders()

        self.limit_raw_sql = limit_raw_sql

    def _init_sorted_orders(self) -> None:
        """
        Initialize empty order_by dict to be populated later during the query call
        """
        if self.order_columns:
            for clause in self.order_columns:
                self.sorted_orders[clause] = None

    def apply_order_bys_for_primary_model(self) -> None:  # noqa: CCR001
        """
        Applies order_by queries on main model when it's used as a subquery.
        That way the subquery with limit and offset only on main model has proper
        sorting applied and correct models are fetched.
        """
        if self.order_columns:
            for clause in self.order_columns:
                if clause.is_source_model_order:
                    self.sorted_orders[clause] = clause.get_text_clause()
        else:
            clause = ormar.OrderAction(
                order_str=self.model_cls.Meta.pkname, model_cls=self.model_cls
            )
            self.sorted_orders[clause] = clause.get_text_clause()

    def _pagination_query_required(self) -> bool:
        """
        Checks if limit or offset are set, the flag limit_sql_raw is not set
        and query has select_related applied. Otherwise we can limit/offset normally
        at the end of whole query.

        :return: result of the check
        :rtype: bool
        """
        return bool(
            (self.limit_count or self.query_offset)
            and not self.limit_raw_sql
            and self._select_related
        )

    def build_select_expression(self) -> Tuple[sqlalchemy.sql.select, List[str]]:
        """
        Main entry point from outside (after proper initialization).

        Extracts columns list to fetch,
        construct all required joins for select related,
        then applies all conditional and sort clauses.

        Returns ready to run query with all joins and clauses.

        :return: ready to run query with all joins and clauses.
        :rtype: sqlalchemy.sql.selectable.Select
        """
        self_related_fields = self.model_cls.own_table_columns(
            model=self.model_cls, excludable=self.excludable, use_alias=True,
        )
        self.columns = self.model_cls.Meta.alias_manager.prefixed_columns(
            "", self.table, self_related_fields
        )
        self.apply_order_bys_for_primary_model()
        if self._pagination_query_required():
            self.select_from = self._build_pagination_subquery()
        else:
            self.select_from = self.table

        related_models = group_related_list(self._select_related)

        for related in related_models:
            remainder = None
            if isinstance(related_models, dict) and related_models[related]:
                remainder = related_models[related]
            sql_join = SqlJoin(
                used_aliases=self.used_aliases,
                select_from=self.select_from,
                columns=self.columns,
                excludable=self.excludable,
                order_columns=self.order_columns,
                sorted_orders=self.sorted_orders,
                main_model=self.model_cls,
                relation_name=related,
                relation_str=related,
                related_models=remainder,
            )

            (
                self.used_aliases,
                self.select_from,
                self.columns,
                self.sorted_orders,
            ) = sql_join.build_join()

        expr = sqlalchemy.sql.select(self.columns)
        expr = expr.select_from(self.select_from)

        expr = self._apply_expression_modifiers(expr)

        # print("\n", expr.compile(compile_kwargs={"literal_binds": True}))
        self._reset_query_parameters()

        return expr

    def _build_pagination_subquery(self) -> sqlalchemy.sql.select:
        """
        In order to apply limit and offset on main table in join only
        (otherwise you can get only partially constructed main model
        if number of children exceeds the applied limit and select_related is used)

        Used also to change first and get() without argument behaviour.
        Needed only if limit or offset are set, the flag limit_sql_raw is not set
        and query has select_related applied. Otherwise we can limit/offset normally
        at the end of whole query.

        :return: constructed subquery on main table with limit, offset and order applied
        :rtype: sqlalchemy.sql.select
        """
        expr = sqlalchemy.sql.select(self.model_cls.Meta.table.columns)
        expr = LimitQuery(limit_count=self.limit_count).apply(expr)
        expr = OffsetQuery(query_offset=self.query_offset).apply(expr)
        filters_to_use = [
            filter_clause
            for filter_clause in self.filter_clauses
            if filter_clause.is_source_model_filter
        ]
        excludes_to_use = [
            filter_clause
            for filter_clause in self.exclude_clauses
            if filter_clause.is_source_model_filter
        ]
        sorts_to_use = {
            k: v for k, v in self.sorted_orders.items() if k.is_source_model_order
        }
        expr = FilterQuery(filter_clauses=filters_to_use).apply(expr)
        expr = FilterQuery(filter_clauses=excludes_to_use, exclude=True).apply(expr)
        expr = OrderQuery(sorted_orders=sorts_to_use).apply(expr)
        expr = expr.alias(f"{self.table}")
        self.filter_clauses = list(set(self.filter_clauses) - set(filters_to_use))
        self.exclude_clauses = list(set(self.exclude_clauses) - set(excludes_to_use))
        return expr

    def _apply_expression_modifiers(
        self, expr: sqlalchemy.sql.select
    ) -> sqlalchemy.sql.select:
        """
        Receives the select query (might be join) and applies:
        * Filter clauses
        * Exclude filter clauses
        * Limit clauses
        * Offset clauses
        * Order by clauses

        Returns complete ready to run query.

        :param expr: select expression before clauses
        :type expr: sqlalchemy.sql.selectable.Select
        :return: expresion with all present clauses applied
        :rtype: sqlalchemy.sql.selectable.Select
        """
        expr = FilterQuery(filter_clauses=self.filter_clauses).apply(expr)
        expr = FilterQuery(filter_clauses=self.exclude_clauses, exclude=True).apply(
            expr
        )
        if not self._pagination_query_required():
            expr = LimitQuery(limit_count=self.limit_count).apply(expr)
            expr = OffsetQuery(query_offset=self.query_offset).apply(expr)
        expr = OrderQuery(sorted_orders=self.sorted_orders).apply(expr)
        return expr

    def _reset_query_parameters(self) -> None:
        """
        Although it should be created each time before the call we reset the key params
        anyway.
        """
        self.select_from = []
        self.columns = []
        self.used_aliases = []
