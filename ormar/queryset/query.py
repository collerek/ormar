import copy
from collections import OrderedDict
from typing import Dict, List, Optional, Set, TYPE_CHECKING, Tuple, Type, Union

import sqlalchemy
from sqlalchemy import text

import ormar  # noqa I100
from ormar.queryset import FilterQuery, LimitQuery, OffsetQuery, OrderQuery
from ormar.queryset.join import JoinParameters, SqlJoin

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


class Query:
    def __init__(  # noqa CFQ002
        self,
        model_cls: Type["Model"],
        filter_clauses: List,
        exclude_clauses: List,
        select_related: List,
        limit_count: Optional[int],
        offset: Optional[int],
        fields: Optional[Union[Dict, Set]],
        exclude_fields: Optional[Union[Dict, Set]],
        order_bys: Optional[List],
        limit_raw_sql: bool,
    ) -> None:
        self.query_offset = offset
        self.limit_count = limit_count
        self._select_related = select_related[:]
        self.filter_clauses = filter_clauses[:]
        self.exclude_clauses = exclude_clauses[:]
        self.fields = copy.deepcopy(fields) if fields else {}
        self.exclude_fields = copy.deepcopy(exclude_fields) if exclude_fields else {}

        self.model_cls = model_cls
        self.table = self.model_cls.Meta.table

        self.used_aliases: List[str] = []

        self.select_from: List[str] = []
        self.columns = [sqlalchemy.Column]
        self.order_columns = order_bys
        self.sorted_orders: OrderedDict = OrderedDict()
        self._init_sorted_orders()

        self.limit_raw_sql = limit_raw_sql

    def _init_sorted_orders(self) -> None:
        if self.order_columns:
            for clause in self.order_columns:
                self.sorted_orders[clause] = None

    @property
    def prefixed_pk_name(self) -> str:
        pkname_alias = self.model_cls.get_column_alias(self.model_cls.Meta.pkname)
        return f"{self.table.name}.{pkname_alias}"

    def alias(self, name: str) -> str:
        return self.model_cls.get_column_alias(name)

    def apply_order_bys_for_primary_model(self) -> None:  # noqa: CCR001
        if self.order_columns:
            for clause in self.order_columns:
                if "__" not in clause:
                    text_clause = (
                        text(f"{self.alias(clause[1:])} desc")
                        if clause.startswith("-")
                        else text(self.alias(clause))
                    )
                    self.sorted_orders[clause] = text_clause
        else:
            order = text(self.prefixed_pk_name)
            self.sorted_orders[self.prefixed_pk_name] = order

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
        self_related_fields = self.model_cls.own_table_columns(
            model=self.model_cls,
            fields=self.fields,
            exclude_fields=self.exclude_fields,
            use_alias=True,
        )
        self.columns = self.model_cls.Meta.alias_manager.prefixed_columns(
            "", self.table, self_related_fields
        )
        self.apply_order_bys_for_primary_model()
        if self._pagination_query_required():
            self.select_from = self._build_pagination_subquery()
        else:
            self.select_from = self.table

        self._select_related.sort(key=lambda item: (item, -len(item)))

        for item in self._select_related:
            join_parameters = JoinParameters(
                self.model_cls, "", self.table.name, self.model_cls
            )
            fields = self.model_cls.get_included(self.fields, item)
            exclude_fields = self.model_cls.get_excluded(self.exclude_fields, item)
            sql_join = SqlJoin(
                used_aliases=self.used_aliases,
                select_from=self.select_from,
                columns=self.columns,
                fields=fields,
                exclude_fields=exclude_fields,
                order_columns=self.order_columns,
                sorted_orders=self.sorted_orders,
            )

            (
                self.used_aliases,
                self.select_from,
                self.columns,
                self.sorted_orders,
            ) = sql_join.build_join(item, join_parameters)

        expr = sqlalchemy.sql.select(self.columns)
        expr = expr.select_from(self.select_from)

        expr = self._apply_expression_modifiers(expr)

        # print(expr.compile(compile_kwargs={"literal_binds": True}))
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
            if filter_clause.text.startswith(f"{self.table.name}.")
        ]
        excludes_to_use = [
            filter_clause
            for filter_clause in self.exclude_clauses
            if filter_clause.text.startswith(f"{self.table.name}.")
        ]
        sorts_to_use = {
            k: v
            for k, v in self.sorted_orders.items()
            if k.startswith(f"{self.table.name}.")
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
        self.select_from = []
        self.columns = []
        self.used_aliases = []
        self.fields = {}
        self.exclude_fields = {}
