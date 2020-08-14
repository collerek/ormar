from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple, Type, Union

import sqlalchemy
from sqlalchemy import text

import ormar  # noqa I100
from ormar.exceptions import QueryDefinitionError

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model

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

        if op not in ["contains", "icontains"]:
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
