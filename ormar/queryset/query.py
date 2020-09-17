from typing import List, NamedTuple, TYPE_CHECKING, Tuple, Type

import sqlalchemy
from sqlalchemy import text

import ormar  # noqa I100
from ormar.fields.many_to_many import ManyToManyField
from ormar.queryset import FilterQuery, LimitQuery, OffsetQuery, OrderQuery
from ormar.relations.alias_manager import AliasManager

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
                if issubclass(
                    join_parameters.model_cls.Meta.model_fields[part], ManyToManyField
                ):
                    _fields = join_parameters.model_cls.Meta.model_fields
                    new_part = _fields[part].to.get_name()
                    join_parameters = self._build_join_parameters(
                        part, join_parameters, is_multi=True
                    )
                    part = new_part
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
        self, part: str, join_params: JoinParameters, is_multi: bool = False
    ) -> JoinParameters:
        if is_multi:
            model_cls = join_params.model_cls.Meta.model_fields[part].through
        else:
            model_cls = join_params.model_cls.Meta.model_fields[part].to
        to_table = model_cls.Meta.table.name

        alias = model_cls.Meta.alias_manager.resolve_relation_join(
            join_params.from_table, to_table
        )
        if alias not in self.used_aliases:
            self._process_join(join_params, is_multi, model_cls, part, alias)

        previous_alias = alias
        from_table = to_table
        prev_model = model_cls
        return JoinParameters(prev_model, previous_alias, from_table, model_cls)

    def _process_join(
        self,
        join_params: JoinParameters,
        is_multi: bool,
        model_cls: Type["Model"],
        part: str,
        alias: str,
    ) -> None:
        to_table = model_cls.Meta.table.name
        to_key, from_key = self._get_to_and_from_keys(
            join_params, is_multi, model_cls, part
        )

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

    def _get_to_and_from_keys(
        self,
        join_params: JoinParameters,
        is_multi: bool,
        model_cls: Type["Model"],
        part: str,
    ) -> Tuple[str, str]:
        if join_params.prev_model.Meta.model_fields[part].virtual or is_multi:
            to_field = model_cls.resolve_relation_field(
                model_cls, join_params.prev_model
            )
            to_key = to_field.name
            from_key = model_cls.Meta.pkname
        else:
            to_key = model_cls.Meta.pkname
            from_key = part
        return to_key, from_key

    def _apply_expression_modifiers(
        self, expr: sqlalchemy.sql.select
    ) -> sqlalchemy.sql.select:
        expr = FilterQuery(filter_clauses=self.filter_clauses).apply(expr)
        expr = LimitQuery(limit_count=self.limit_count).apply(expr)
        expr = OffsetQuery(query_offset=self.query_offset).apply(expr)
        expr = OrderQuery(order_bys=self.order_bys).apply(expr)
        return expr

    def _reset_query_parameters(self) -> None:
        self.select_from = None
        self.columns = None
        self.order_bys = None
        self.used_aliases = []
