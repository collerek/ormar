from typing import List, NamedTuple, TYPE_CHECKING, Tuple, Type

import sqlalchemy
from sqlalchemy import text

import ormar  # noqa I100
from ormar.fields.foreign_key import ForeignKeyField
from ormar.relations import AliasManager

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


class JoinParameters(NamedTuple):
    prev_model: Type["Model"]
    previous_alias: str
    from_table: str
    model_cls: Type["Model"]


class Query:
    def __init__(
        self,
        model_cls: Type["Model"],
        filter_clauses: List,
        select_related: List,
        limit_count: int,
        offset: int,
    ) -> None:

        self.query_offset = offset
        self.limit_count = limit_count
        self._select_related = select_related
        self.filter_clauses = filter_clauses

        self.model_cls = model_cls
        self.table = self.model_cls.Meta.table

        self.used_aliases = []

        self.select_from = None
        self.columns = None
        self.order_bys = None

    @property
    def relation_manager(self) -> AliasManager:
        return self.model_cls.Meta.alias_manager

    @property
    def prefixed_pk_name(self) -> str:
        return f"{self.table.name}.{self.model_cls.Meta.pkname}"

    def build_select_expression(self) -> Tuple[sqlalchemy.sql.select, List[str]]:
        self.columns = list(self.table.columns)
        self.order_bys = [text(self.prefixed_pk_name)]
        self.select_from = self.table

        self._select_related.sort(key=lambda item: (item, -len(item)))

        for item in self._select_related:
            join_parameters = JoinParameters(
                self.model_cls, "", self.table.name, self.model_cls
            )

            for part in item.split("__"):
                join_parameters = self._build_join_parameters(part, join_parameters)

        expr = sqlalchemy.sql.select(self.columns)
        expr = expr.select_from(self.select_from)

        expr = self._apply_expression_modifiers(expr)

        # print(expr.compile(compile_kwargs={"literal_binds": True}))
        self._reset_query_parameters()

        return expr

    @staticmethod
    def on_clause(
        previous_alias: str, alias: str, from_clause: str, to_clause: str,
    ) -> text:
        left_part = f"{alias}_{to_clause}"
        right_part = f"{previous_alias + '_' if previous_alias else ''}{from_clause}"
        return text(f"{left_part}={right_part}")

    def _build_join_parameters(
        self, part: str, join_params: JoinParameters
    ) -> JoinParameters:
        model_cls = join_params.model_cls.Meta.model_fields[part].to
        to_table = model_cls.Meta.table.name

        alias = model_cls.Meta.alias_manager.resolve_relation_join(
            join_params.from_table, to_table
        )
        if alias not in self.used_aliases:
            if join_params.prev_model.Meta.model_fields[part].virtual:
                to_key = next(
                    (
                        v
                        for k, v in model_cls.Meta.model_fields.items()
                        if issubclass(v, ForeignKeyField)
                        and v.to == join_params.prev_model
                    ),
                    None,
                ).name
                from_key = model_cls.Meta.pkname
            else:
                to_key = model_cls.Meta.pkname
                from_key = part

            on_clause = self.on_clause(
                previous_alias=join_params.previous_alias,
                alias=alias,
                from_clause=f"{join_params.from_table}.{from_key}",
                to_clause=f"{to_table}.{to_key}",
            )
            target_table = self.relation_manager.prefixed_table_name(alias, to_table)
            self.select_from = sqlalchemy.sql.outerjoin(
                self.select_from, target_table, on_clause
            )
            self.order_bys.append(text(f"{alias}_{to_table}.{model_cls.Meta.pkname}"))
            self.columns.extend(
                self.relation_manager.prefixed_columns(alias, model_cls.Meta.table)
            )
            self.used_aliases.append(alias)

        previous_alias = alias
        from_table = to_table
        prev_model = model_cls
        return JoinParameters(prev_model, previous_alias, from_table, model_cls)

    def _apply_expression_modifiers(
        self, expr: sqlalchemy.sql.select
    ) -> sqlalchemy.sql.select:
        if self.filter_clauses:
            if len(self.filter_clauses) == 1:
                clause = self.filter_clauses[0]
            else:
                clause = sqlalchemy.sql.and_(*self.filter_clauses)
            expr = expr.where(clause)

        if self.limit_count:
            expr = expr.limit(self.limit_count)

        if self.query_offset:
            expr = expr.offset(self.query_offset)

        for order in self.order_bys:
            expr = expr.order_by(order)
        return expr

    def _reset_query_parameters(self) -> None:
        self.select_from = None
        self.columns = None
        self.order_bys = None
        self.used_aliases = []
