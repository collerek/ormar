from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple, Type

import sqlalchemy
from sqlalchemy import text

import ormar  # noqa I100
from ormar.exceptions import QueryDefinitionError
from ormar.fields.many_to_many import ManyToManyField

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model

FILTER_OPERATORS = {
    "exact": "__eq__",
    "iexact": "ilike",
    "contains": "like",
    "icontains": "ilike",
    "startswith": "like",
    "istartswith": "ilike",
    "endswith": "like",
    "iendswith": "ilike",
    "in": "in_",
    "gt": "__gt__",
    "gte": "__ge__",
    "lt": "__lt__",
    "lte": "__le__",
}
ESCAPE_CHARACTERS = ["%", "_"]


class QueryClause:
    def __init__(
        self, model_cls: Type["Model"], filter_clauses: List, select_related: List,
    ) -> None:

        self._select_related = select_related[:]
        self.filter_clauses = filter_clauses[:]

        self.model_cls = model_cls
        self.table = self.model_cls.Meta.table

    def filter(  # noqa: A003
        self, **kwargs: Any
    ) -> Tuple[List[sqlalchemy.sql.expression.TextClause], List[str]]:

        if kwargs.get("pk"):
            pk_name = self.model_cls.get_column_alias(self.model_cls.Meta.pkname)
            kwargs[pk_name] = kwargs.pop("pk")

        filter_clauses, select_related = self._populate_filter_clauses(**kwargs)

        return filter_clauses, select_related

    def _populate_filter_clauses(
        self, **kwargs: Any
    ) -> Tuple[List[sqlalchemy.sql.expression.TextClause], List[str]]:
        filter_clauses = self.filter_clauses
        select_related = list(self._select_related)

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

                table = model_cls.Meta.table
                column = model_cls.Meta.table.columns[field_name]

            else:
                op = "exact"
                column = self.table.columns[self.model_cls.get_column_alias(key)]
                table = self.table

            clause = self._process_column_clause_for_operator_and_value(
                value, op, column, table, table_prefix
            )
            filter_clauses.append(clause)
        return filter_clauses, select_related

    def _process_column_clause_for_operator_and_value(
        self,
        value: Any,
        op: str,
        column: sqlalchemy.Column,
        table: sqlalchemy.Table,
        table_prefix: str,
    ) -> sqlalchemy.sql.expression.TextClause:
        value, has_escaped_character = self._escape_characters_in_clause(op, value)

        if isinstance(value, ormar.Model):
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
        return clause

    def _determine_filter_target_table(
        self, related_parts: List[str], select_related: List[str]
    ) -> Tuple[List[str], str, Type["Model"]]:

        table_prefix = ""
        model_cls = self.model_cls
        select_related = [relation for relation in select_related]

        # Add any implied select_related
        related_str = "__".join(related_parts)
        if related_str not in select_related:
            select_related.append(related_str)

        # Walk the relationships to the actual model class
        # against which the comparison is being made.
        previous_table = model_cls.Meta.tablename
        for part in related_parts:
            if issubclass(model_cls.Meta.model_fields[part], ManyToManyField):
                previous_table = model_cls.Meta.model_fields[
                    part
                ].through.Meta.tablename
            current_table = model_cls.Meta.model_fields[part].to.Meta.tablename
            manager = model_cls.Meta.alias_manager
            table_prefix = manager.resolve_relation_join(previous_table, current_table)
            model_cls = model_cls.Meta.model_fields[part].to
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
                dialect=self.model_cls.Meta.database._backend._dialect,
                compile_kwargs={"literal_binds": True},
            )
        )
        alias = f"{table_prefix}_" if table_prefix else ""
        aliased_name = f"{alias}{table.name}.{column.name}"
        clause_text = clause_text.replace(f"{table.name}.{column.name}", aliased_name)
        clause = text(clause_text)
        return clause

    @staticmethod
    def _escape_characters_in_clause(op: str, value: Any) -> Tuple[Any, bool]:
        has_escaped_character = False

        if op not in [
            "contains",
            "icontains",
            "startswith",
            "istartswith",
            "endswith",
            "iendswith",
        ]:
            return value, has_escaped_character

        if isinstance(value, ormar.Model):
            raise QueryDefinitionError(
                "You cannot use contains and icontains with instance of the Model"
            )

        has_escaped_character = any(c for c in ESCAPE_CHARACTERS if c in value)

        if has_escaped_character:
            # enable escape modifier
            for char in ESCAPE_CHARACTERS:
                value = value.replace(char, f"\\{char}")
        prefix = "%" if "start" not in op else ""
        sufix = "%" if "end" not in op else ""
        value = f"{prefix}{value}{sufix}"

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
