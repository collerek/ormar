from typing import List, Optional, TYPE_CHECKING, Tuple, Type

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
        fields: Optional[List],
    ) -> None:
        self.query_offset = offset
        self.limit_count = limit_count
        self._select_related = select_related[:]
        self.filter_clauses = filter_clauses[:]
        self.exclude_clauses = exclude_clauses[:]
        self.fields = fields[:] if fields else []

        self.model_cls = model_cls
        self.table = self.model_cls.Meta.table

        self.used_aliases: List[str] = []

        self.select_from: List[str] = []
        self.columns = [sqlalchemy.Column]
        self.order_bys: List[sqlalchemy.sql.elements.TextClause] = []

    @property
    def prefixed_pk_name(self) -> str:
        return f"{self.table.name}.{self.model_cls.Meta.pkname}"

    def build_select_expression(self) -> Tuple[sqlalchemy.sql.select, List[str]]:
        self_related_fields = self.model_cls.own_table_columns(
            self.model_cls, self.fields
        )
        self.columns = self.model_cls.Meta.alias_manager.prefixed_columns(
            "", self.table, self_related_fields
        )
        self.order_bys = [text(self.prefixed_pk_name)]
        self.select_from = self.table

        self._select_related.sort(key=lambda item: (item, -len(item)))

        for item in self._select_related:
            join_parameters = JoinParameters(
                self.model_cls, "", self.table.name, self.model_cls
            )

            sql_join = SqlJoin(
                used_aliases=self.used_aliases,
                select_from=self.select_from,
                columns=self.columns,
                order_bys=self.order_bys,
                fields=self.fields,
            )

            (
                self.used_aliases,
                self.select_from,
                self.columns,
                self.order_bys,
            ) = sql_join.build_join(item, join_parameters)

        expr = sqlalchemy.sql.select(self.columns)
        expr = expr.select_from(self.select_from)

        expr = self._apply_expression_modifiers(expr)

        # print(expr.compile(compile_kwargs={"literal_binds": True}))
        self._reset_query_parameters()

        return expr

    def _apply_expression_modifiers(
        self, expr: sqlalchemy.sql.select
    ) -> sqlalchemy.sql.select:
        expr = FilterQuery(filter_clauses=self.filter_clauses).apply(expr)
        expr = FilterQuery(filter_clauses=self.exclude_clauses, exclude=True).apply(
            expr
        )
        expr = LimitQuery(limit_count=self.limit_count).apply(expr)
        expr = OffsetQuery(query_offset=self.query_offset).apply(expr)
        expr = OrderQuery(order_bys=self.order_bys).apply(expr)
        return expr

    def _reset_query_parameters(self) -> None:
        self.select_from = []
        self.columns = []
        self.order_bys = []
        self.used_aliases = []
        self.fields = []
