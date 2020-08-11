from typing import (
    Any,
    Dict,
    List,
    NamedTuple,
    Optional,
    TYPE_CHECKING,
    Tuple,
    Type,
    Union,
)

import databases
import sqlalchemy
from sqlalchemy import text

import orm  # noqa I100
import orm.fields.foreign_key
from orm import ForeignKey
from orm.exceptions import MultipleMatches, NoMatch, QueryDefinitionError
from orm.fields.base import BaseField

if TYPE_CHECKING:  # pragma no cover
    from orm.models import Model

FILTER_OPERATORS = {
    "exact": "__eq__",
    "iexact": "ilike",
    "contains": "like",
    "icontains": "ilike",
    "in": "in_",
    "gt": "__gt__",
    "gte": "__ge__",
    "lt": "__lt__",
    "lte": "__le__",
}

ESCAPE_CHARACTERS = ["%", "_"]


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
                    self.model_cls.__model_fields__[key],
                    orm.fields.foreign_key.ForeignKey,
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
        already_checked = any([x.startswith(rel_part) for x in self.auto_related])
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


class QueryClause:
    def __init__(
        self, model_cls: Type["Model"], filter_clauses: List, select_related: List,
    ) -> None:

        self._select_related = select_related
        self.filter_clauses = filter_clauses

        self.model_cls = model_cls
        self.table = self.model_cls.__table__

    def filter(  # noqa: A003
        self, **kwargs: Any
    ) -> Tuple[List[sqlalchemy.sql.expression.TextClause], List[str]]:
        filter_clauses = self.filter_clauses
        select_related = list(self._select_related)

        if kwargs.get("pk"):
            pk_name = self.model_cls.__pkname__
            kwargs[pk_name] = kwargs.pop("pk")

        for key, value in kwargs.items():
            table_prefix = ""
            if "__" in key:
                parts = key.split("__")

                (
                    op,
                    field_name,
                    related_parts,
                ) = self._extract_operator_field_and_related(parts)

                model_cls = self.model_cls
                if related_parts:
                    (
                        select_related,
                        table_prefix,
                        model_cls,
                    ) = self._determine_filter_target_table(
                        related_parts, select_related
                    )

                table = model_cls.__table__
                column = model_cls.__table__.columns[field_name]

            else:
                op = "exact"
                column = self.table.columns[key]
                table = self.table

            value, has_escaped_character = self._escape_characters_in_clause(op, value)

            if isinstance(value, orm.Model):
                value = value.pk

            op_attr = FILTER_OPERATORS[op]
            clause = getattr(column, op_attr)(value)
            clause = self._compile_clause(
                clause,
                column,
                table,
                table_prefix,
                modifiers={"escape": "\\" if has_escaped_character else None},
            )
            filter_clauses.append(clause)

        return filter_clauses, select_related

    def _determine_filter_target_table(
        self, related_parts: List[str], select_related: List[str]
    ) -> Tuple[List[str], str, "Model"]:

        table_prefix = ""
        model_cls = self.model_cls
        select_related = [relation for relation in select_related]

        # Add any implied select_related
        related_str = "__".join(related_parts)
        if related_str not in select_related:
            select_related.append(related_str)

        # Walk the relationships to the actual model class
        # against which the comparison is being made.
        previous_table = model_cls.__tablename__
        for part in related_parts:
            current_table = model_cls.__model_fields__[part].to.__tablename__
            manager = model_cls._orm_relationship_manager
            table_prefix = manager.resolve_relation_join(previous_table, current_table)
            model_cls = model_cls.__model_fields__[part].to
            previous_table = current_table
        return select_related, table_prefix, model_cls

    def _compile_clause(
        self,
        clause: sqlalchemy.sql.expression.BinaryExpression,
        column: sqlalchemy.Column,
        table: sqlalchemy.Table,
        table_prefix: str,
        modifiers: Dict,
    ) -> sqlalchemy.sql.expression.TextClause:
        for modifier, modifier_value in modifiers.items():
            clause.modifiers[modifier] = modifier_value

        clause_text = str(
            clause.compile(
                dialect=self.model_cls.__database__._backend._dialect,
                compile_kwargs={"literal_binds": True},
            )
        )
        alias = f"{table_prefix}_" if table_prefix else ""
        aliased_name = f"{alias}{table.name}.{column.name}"
        clause_text = clause_text.replace(f"{table.name}.{column.name}", aliased_name)
        clause = text(clause_text)
        return clause

    @staticmethod
    def _escape_characters_in_clause(
        op: str, value: Union[str, "Model"]
    ) -> Tuple[str, bool]:
        has_escaped_character = False

        if op in ["contains", "icontains"]:
            if isinstance(value, orm.Model):
                raise QueryDefinitionError(
                    "You cannot use contains and icontains with instance of the Model"
                )

            has_escaped_character = any(c for c in ESCAPE_CHARACTERS if c in value)

            if has_escaped_character:
                # enable escape modifier
                for char in ESCAPE_CHARACTERS:
                    value = value.replace(char, f"\\{char}")
            value = f"%{value}%"

        return value, has_escaped_character

    @staticmethod
    def _extract_operator_field_and_related(
        parts: List[str],
    ) -> Tuple[str, str, Optional[List]]:
        if parts[-1] in FILTER_OPERATORS:
            op = parts[-1]
            field_name = parts[-2]
            related_parts = parts[:-2]
        else:
            op = "exact"
            field_name = parts[-1]
            related_parts = parts[:-1]

        return op, field_name, related_parts


class QuerySet:
    def __init__(
        self,
        model_cls: Type["Model"] = None,
        filter_clauses: List = None,
        select_related: List = None,
        limit_count: int = None,
        offset: int = None,
    ) -> None:
        self.model_cls = model_cls
        self.filter_clauses = [] if filter_clauses is None else filter_clauses
        self._select_related = [] if select_related is None else select_related
        self.limit_count = limit_count
        self.query_offset = offset
        self.order_bys = None

    def __get__(self, instance: "QuerySet", owner: Type["Model"]) -> "QuerySet":
        return self.__class__(model_cls=owner)

    @property
    def database(self) -> databases.Database:
        return self.model_cls.__database__

    @property
    def table(self) -> sqlalchemy.Table:
        return self.model_cls.__table__

    def build_select_expression(self) -> sqlalchemy.sql.select:
        qry = Query(
            model_cls=self.model_cls,
            select_related=self._select_related,
            filter_clauses=self.filter_clauses,
            offset=self.query_offset,
            limit_count=self.limit_count,
        )
        exp, self._select_related = qry.build_select_expression()
        return exp

    def filter(self, **kwargs: Any) -> "QuerySet":  # noqa: A003
        qryclause = QueryClause(
            model_cls=self.model_cls,
            select_related=self._select_related,
            filter_clauses=self.filter_clauses,
        )
        filter_clauses, select_related = qryclause.filter(**kwargs)

        return self.__class__(
            model_cls=self.model_cls,
            filter_clauses=filter_clauses,
            select_related=select_related,
            limit_count=self.limit_count,
            offset=self.query_offset,
        )

    def select_related(self, related: Union[List, Tuple, str]) -> "QuerySet":
        if not isinstance(related, (list, tuple)):
            related = [related]

        related = list(self._select_related) + related
        return self.__class__(
            model_cls=self.model_cls,
            filter_clauses=self.filter_clauses,
            select_related=related,
            limit_count=self.limit_count,
            offset=self.query_offset,
        )

    async def exists(self) -> bool:
        expr = self.build_select_expression()
        expr = sqlalchemy.exists(expr).select()
        return await self.database.fetch_val(expr)

    async def count(self) -> int:
        expr = self.build_select_expression().alias("subquery_for_count")
        expr = sqlalchemy.func.count().select().select_from(expr)
        return await self.database.fetch_val(expr)

    def limit(self, limit_count: int) -> "QuerySet":
        return self.__class__(
            model_cls=self.model_cls,
            filter_clauses=self.filter_clauses,
            select_related=self._select_related,
            limit_count=limit_count,
            offset=self.query_offset,
        )

    def offset(self, offset: int) -> "QuerySet":
        return self.__class__(
            model_cls=self.model_cls,
            filter_clauses=self.filter_clauses,
            select_related=self._select_related,
            limit_count=self.limit_count,
            offset=offset,
        )

    async def first(self, **kwargs: Any) -> "Model":
        if kwargs:
            return await self.filter(**kwargs).first()

        rows = await self.limit(1).all()
        if rows:
            return rows[0]

    async def get(self, **kwargs: Any) -> "Model":
        if kwargs:
            return await self.filter(**kwargs).get()

        expr = self.build_select_expression().limit(2)
        rows = await self.database.fetch_all(expr)

        if not rows:
            raise NoMatch()
        if len(rows) > 1:
            raise MultipleMatches()
        return self.model_cls.from_row(rows[0], select_related=self._select_related)

    async def all(self, **kwargs: Any) -> List["Model"]:  # noqa: A003
        if kwargs:
            return await self.filter(**kwargs).all()

        expr = self.build_select_expression()
        rows = await self.database.fetch_all(expr)
        result_rows = [
            self.model_cls.from_row(row, select_related=self._select_related)
            for row in rows
        ]

        result_rows = self.model_cls.merge_instances_list(result_rows)

        return result_rows

    async def create(self, **kwargs: Any) -> "Model":

        new_kwargs = dict(**kwargs)

        # Remove primary key when None to prevent not null constraint in postgresql.
        pkname = self.model_cls.__pkname__
        pk = self.model_cls.__model_fields__[pkname]
        if (
            pkname in new_kwargs
            and new_kwargs.get(pkname) is None
            and (pk.nullable or pk.autoincrement)
        ):
            del new_kwargs[pkname]

        # substitute related models with their pk
        for field in self.model_cls._extract_related_names():
            if field in new_kwargs and new_kwargs.get(field) is not None:
                new_kwargs[field] = getattr(
                    new_kwargs.get(field),
                    self.model_cls.__model_fields__[field].to.__pkname__,
                )

        # Build the insert expression.
        expr = self.table.insert()
        expr = expr.values(**new_kwargs)

        # Execute the insert, and return a new model instance.
        instance = self.model_cls(**kwargs)
        instance.pk = await self.database.execute(expr)
        return instance
