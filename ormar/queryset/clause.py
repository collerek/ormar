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
    """
    Constructs where clauses from strings passed as arguments
    """

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
        """
        Main external access point that processes the clauses into sqlalchemy text
        clauses and updates select_related list with implicit related tables
        mentioned in select_related strings but not included in select_related.

        :param kwargs: key, value pair with column names and values
        :type kwargs: Any
        :return: Tuple with list of where clauses and updated select_related list
        :rtype: Tuple[List[sqlalchemy.sql.elements.TextClause], List[str]]
        """
        if kwargs.get("pk"):
            pk_name = self.model_cls.get_column_alias(self.model_cls.Meta.pkname)
            kwargs[pk_name] = kwargs.pop("pk")

        filter_clauses, select_related = self._populate_filter_clauses(**kwargs)

        return filter_clauses, select_related

    def _populate_filter_clauses(
        self, **kwargs: Any
    ) -> Tuple[List[sqlalchemy.sql.expression.TextClause], List[str]]:
        """
        Iterates all clauses and extracts used operator and field from related
        models if needed. Based on the chain of related names the target table
        is determined and the final clause is escaped if needed and compiled.

        :param kwargs: key, value pair with column names and values
        :type kwargs: Any
        :return: Tuple with list of where clauses and updated select_related list
        :rtype: Tuple[List[sqlalchemy.sql.elements.TextClause], List[str]]
        """
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
        """
        Escapes characters if it's required.
        Substitutes values of the models if value is a ormar Model with its pk value.
        Compiles the clause.

        :param value: value of the filter
        :type value: Any
        :param op: filter operator
        :type op: str
        :param column: column on which filter should be applied
        :type column: sqlalchemy.sql.schema.Column
        :param table: table on which filter should be applied
        :type table: sqlalchemy.sql.schema.Table
        :param table_prefix: prefix from AliasManager
        :type table_prefix: str
        :return: complied and escaped clause
        :rtype: sqlalchemy.sql.elements.TextClause
        """
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
        """
        Adds related strings to select_related list otherwise the clause would fail as
        the required columns would not be present. That means that select_related
        list is filled with missing values present in filters.

        Walks the relation to retrieve the actual model on which the clause should be
        constructed, extracts alias based on last relation leading to target model.

        :param related_parts: list of split parts of related string
        :type related_parts: List[str]
        :param select_related: list of related models
        :type select_related: List[str]
        :return: list of related models, table_prefix, final model class
        :rtype: Tuple[List[str], str, Type[Model]]
        """
        table_prefix = ""
        model_cls = self.model_cls
        select_related = [relation for relation in select_related]

        # Add any implied select_related
        related_str = "__".join(related_parts)
        if related_str not in select_related:
            select_related.append(related_str)

        # Walk the relationships to the actual model class
        # against which the comparison is being made.
        previous_model = model_cls
        for part in related_parts:
            part2 = part
            if issubclass(model_cls.Meta.model_fields[part], ManyToManyField):
                through_field = model_cls.Meta.model_fields[part]
                previous_model = through_field.through
                part2 = through_field.default_target_field_name()  # type: ignore
            manager = model_cls.Meta.alias_manager
            table_prefix = manager.resolve_relation_alias(previous_model, part2)
            model_cls = model_cls.Meta.model_fields[part].to
            previous_model = model_cls
        return select_related, table_prefix, model_cls

    def _compile_clause(
        self,
        clause: sqlalchemy.sql.expression.BinaryExpression,
        column: sqlalchemy.Column,
        table: sqlalchemy.Table,
        table_prefix: str,
        modifiers: Dict,
    ) -> sqlalchemy.sql.expression.TextClause:
        """
        Compiles the clause to str using appropriate database dialect, replace columns
        names with aliased names and converts it back to TextClause.

        :param clause: original not compiled clause
        :type clause: sqlalchemy.sql.elements.BinaryExpression
        :param column: column on which filter should be applied
        :type column: sqlalchemy.sql.schema.Column
        :param table: table on which filter should be applied
        :type table: sqlalchemy.sql.schema.Table
        :param table_prefix: prefix from AliasManager
        :type table_prefix: str
        :param modifiers: sqlalchemy modifiers - used only to escape chars here
        :type modifiers: Dict[str, NoneType]
        :return: compiled and escaped clause
        :rtype: sqlalchemy.sql.elements.TextClause
        """
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
        """
        Escapes the special characters ["%", "_"] if needed.
        Adds `%` for `like` queries.

        :raises QueryDefinitionError: if contains or icontains is used with
        ormar model instance
        :param op: operator used in query
        :type op: str
        :param value: value of the filter
        :type value: Any
        :return: escaped value and flag if escaping is needed
        :rtype: Tuple[Any, bool]
        """
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
        """
        Splits filter query key and extracts required parts.

        :param parts: split filter query key
        :type parts: List[str]
        :return: operator, field_name, list of related parts
        :rtype: Tuple[str, str, Optional[List]]
        """
        if parts[-1] in FILTER_OPERATORS:
            op = parts[-1]
            field_name = parts[-2]
            related_parts = parts[:-2]
        else:
            op = "exact"
            field_name = parts[-1]
            related_parts = parts[:-1]

        return op, field_name, related_parts
