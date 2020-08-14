from typing import List, NamedTuple, TYPE_CHECKING, Tuple, Type

import sqlalchemy
from sqlalchemy import text

import ormar  # noqa I100
from ormar import ForeignKey
from ormar.fields import BaseField

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
        self.table = self.model_cls.__table__

        self.auto_related = []
        self.used_aliases = []
        self.already_checked = []

        self.select_from = None
        self.columns = None
        self.order_bys = None

    def build_select_expression(self) -> Tuple[sqlalchemy.sql.select, List[str]]:
        self.columns = list(self.table.columns)
        self.order_bys = [text(f"{self.table.name}.{self.model_cls.__pkname__}")]
        self.select_from = self.table

        for key in self.model_cls.__model_fields__:
            if (
                not self.model_cls.__model_fields__[key].nullable
                and isinstance(
                    self.model_cls.__model_fields__[key], ormar.fields.ForeignKey,
                )
                and key not in self._select_related
            ):
                self._select_related = [key] + self._select_related

        start_params = JoinParameters(
            self.model_cls, "", self.table.name, self.model_cls
        )
        self._extract_auto_required_relations(prev_model=start_params.prev_model)
        self._include_auto_related_models()
        self._select_related.sort(key=lambda item: (-len(item), item))

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

        return expr, self._select_related

    @staticmethod
    def prefixed_columns(alias: str, table: sqlalchemy.Table) -> List[text]:
        return [
            text(f"{alias}_{table.name}.{column.name} as {alias}_{column.name}")
            for column in table.columns
        ]

    @staticmethod
    def prefixed_table_name(alias: str, name: str) -> text:
        return text(f"{name} {alias}_{name}")

    @staticmethod
    def _field_is_a_foreign_key_and_no_circular_reference(
        field: BaseField, field_name: str, rel_part: str
    ) -> bool:
        return isinstance(field, ForeignKey) and field_name not in rel_part

    def _field_qualifies_to_deeper_search(
        self, field: ForeignKey, parent_virtual: bool, nested: bool, rel_part: str
    ) -> bool:
        prev_part_of_related = "__".join(rel_part.split("__")[:-1])
        partial_match = any(
            [x.startswith(prev_part_of_related) for x in self._select_related]
        )
        already_checked = any(
            [x.startswith(rel_part) for x in (self.auto_related + self.already_checked)]
        )
        return (
            (field.virtual and parent_virtual)
            or (partial_match and not already_checked)
        ) or not nested

    def on_clause(
        self, previous_alias: str, alias: str, from_clause: str, to_clause: str,
    ) -> text:
        left_part = f"{alias}_{to_clause}"
        right_part = f"{previous_alias + '_' if previous_alias else ''}{from_clause}"
        return text(f"{left_part}={right_part}")

    def _build_join_parameters(
        self, part: str, join_params: JoinParameters
    ) -> JoinParameters:
        model_cls = join_params.model_cls.__model_fields__[part].to
        to_table = model_cls.__table__.name

        alias = model_cls._orm_relationship_manager.resolve_relation_join(
            join_params.from_table, to_table
        )
        if alias not in self.used_aliases:
            if join_params.prev_model.__model_fields__[part].virtual:
                to_key = next(
                    (
                        v
                        for k, v in model_cls.__model_fields__.items()
                        if isinstance(v, ForeignKey) and v.to == join_params.prev_model
                    ),
                    None,
                ).name
                from_key = model_cls.__pkname__
            else:
                to_key = model_cls.__pkname__
                from_key = part

            on_clause = self.on_clause(
                previous_alias=join_params.previous_alias,
                alias=alias,
                from_clause=f"{join_params.from_table}.{from_key}",
                to_clause=f"{to_table}.{to_key}",
            )
            target_table = self.prefixed_table_name(alias, to_table)
            self.select_from = sqlalchemy.sql.outerjoin(
                self.select_from, target_table, on_clause
            )
            self.order_bys.append(text(f"{alias}_{to_table}.{model_cls.__pkname__}"))
            self.columns.extend(self.prefixed_columns(alias, model_cls.__table__))
            self.used_aliases.append(alias)

        previous_alias = alias
        from_table = to_table
        prev_model = model_cls
        return JoinParameters(prev_model, previous_alias, from_table, model_cls)

    def _extract_auto_required_relations(
        self,
        prev_model: Type["Model"],
        rel_part: str = "",
        nested: bool = False,
        parent_virtual: bool = False,
    ) -> None:
        for field_name, field in prev_model.__model_fields__.items():
            if self._field_is_a_foreign_key_and_no_circular_reference(
                field, field_name, rel_part
            ):
                rel_part = field_name if not rel_part else rel_part + "__" + field_name
                if not field.nullable:
                    if rel_part not in self._select_related:
                        self.auto_related.append("__".join(rel_part.split("__")[:-1]))
                    rel_part = ""
                elif self._field_qualifies_to_deeper_search(
                    field, parent_virtual, nested, rel_part
                ):
                    self._extract_auto_required_relations(
                        prev_model=field.to,
                        rel_part=rel_part,
                        nested=True,
                        parent_virtual=field.virtual,
                    )
                else:
                    self.already_checked.append(rel_part)
                    rel_part = ""

    def _include_auto_related_models(self) -> None:
        if self.auto_related:
            new_joins = []
            for join in self._select_related:
                if not any([x.startswith(join) for x in self.auto_related]):
                    new_joins.append(join)
            self._select_related = new_joins + self.auto_related

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
        self.auto_related = []
        self.used_aliases = []
        self.already_checked = []
