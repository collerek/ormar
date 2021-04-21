from typing import Any, Dict, TYPE_CHECKING, Type

import sqlalchemy
from sqlalchemy import text

import ormar  # noqa: I100, I202
from ormar.exceptions import QueryDefinitionError
from ormar.queryset.actions.query_action import QueryAction

if TYPE_CHECKING:  # pragma: nocover
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
    "isnull": "is_",
    "in": "in_",
    "gt": "__gt__",
    "gte": "__ge__",
    "lt": "__lt__",
    "lte": "__le__",
}
METHODS_TO_OPERATORS = {
    "__eq__": "exact",
    "__mod__": "contains",
    "__gt__": "gt",
    "__ge__": "gte",
    "__lt__": "lt",
    "__le__": "lte",
    "iexact": "iexact",
    "contains": "contains",
    "icontains": "icontains",
    "startswith": "startswith",
    "istartswith": "istartswith",
    "endswith": "endswith",
    "iendswith": "iendswith",
    "isnull": "isnull",
    "in": "in",
}
ESCAPE_CHARACTERS = ["%", "_"]


class FilterAction(QueryAction):
    """
    Filter Actions is populated by queryset when filter() is called.

    All required params are extracted but kept raw until actual filter clause value
    is required -> then the action is converted into text() clause.

    Extracted in order to easily change table prefixes on complex relations.
    """

    def __init__(self, filter_str: str, value: Any, model_cls: Type["Model"],) -> None:
        super().__init__(query_str=filter_str, model_cls=model_cls)
        self.filter_value = value
        self._escape_characters_in_clause()

    def has_escaped_characters(self) -> bool:
        """Check if value is a string that contains characters to escape"""
        return isinstance(self.filter_value, str) and any(
            c for c in ESCAPE_CHARACTERS if c in self.filter_value
        )

    def _split_value_into_parts(self, query_str: str) -> None:
        parts = query_str.split("__")
        if parts[-1] in FILTER_OPERATORS:
            self.operator = parts[-1]
            self.field_name = parts[-2]
            self.related_parts = parts[:-2]
        else:
            self.operator = "exact"
            self.field_name = parts[-1]
            self.related_parts = parts[:-1]

    def _escape_characters_in_clause(self) -> None:
        """
        Escapes the special characters ["%", "_"] if needed.
        Adds `%` for `like` queries.

        :raises QueryDefinitionError: if contains or icontains is used with
        ormar model instance
        :return: escaped value and flag if escaping is needed
        :rtype: Tuple[Any, bool]
        """
        self.has_escaped_character = False
        if self.operator in [
            "contains",
            "icontains",
            "startswith",
            "istartswith",
            "endswith",
            "iendswith",
        ]:
            if isinstance(self.filter_value, ormar.Model):
                raise QueryDefinitionError(
                    "You cannot use contains and icontains with instance of the Model"
                )
            self.has_escaped_character = self.has_escaped_characters()
            if self.has_escaped_character:
                self._escape_chars()
            self._prefix_suffix_quote()

    def _escape_chars(self) -> None:
        """Actually replaces chars to escape in value"""
        for char in ESCAPE_CHARACTERS:
            self.filter_value = self.filter_value.replace(char, f"\\{char}")

    def _prefix_suffix_quote(self) -> None:
        """
        Adds % to the beginning of the value if operator checks for containment and not
        starts with.

        Adds % to the end of the value if operator checks for containment and not
        end with.
        :return:
        :rtype:
        """
        prefix = "%" if "start" not in self.operator else ""
        sufix = "%" if "end" not in self.operator else ""
        self.filter_value = f"{prefix}{self.filter_value}{sufix}"

    def get_text_clause(self) -> sqlalchemy.sql.expression.TextClause:
        """
        Escapes characters if it's required.
        Substitutes values of the models if value is a ormar Model with its pk value.
        Compiles the clause.

        :return: complied and escaped clause
        :rtype: sqlalchemy.sql.elements.TextClause
        """

        if isinstance(self.filter_value, ormar.Model):
            self.filter_value = self.filter_value.pk

        op_attr = FILTER_OPERATORS[self.operator]
        if self.operator == "isnull":
            op_attr = "is_" if self.filter_value else "isnot"
            self.filter_value = None
        clause = getattr(self.column, op_attr)(self.filter_value)
        clause = self._compile_clause(
            clause, modifiers={"escape": "\\" if self.has_escaped_character else None},
        )
        return clause

    def _compile_clause(
        self, clause: sqlalchemy.sql.expression.BinaryExpression, modifiers: Dict,
    ) -> sqlalchemy.sql.expression.TextClause:
        """
        Compiles the clause to str using appropriate database dialect, replace columns
        names with aliased names and converts it back to TextClause.

        :param clause: original not compiled clause
        :type clause: sqlalchemy.sql.elements.BinaryExpression
        :param modifiers: sqlalchemy modifiers - used only to escape chars here
        :type modifiers: Dict[str, NoneType]
        :return: compiled and escaped clause
        :rtype: sqlalchemy.sql.elements.TextClause
        """
        for modifier, modifier_value in modifiers.items():
            clause.modifiers[modifier] = modifier_value

        clause_text = str(
            clause.compile(
                dialect=self.target_model.Meta.database._backend._dialect,
                compile_kwargs={"literal_binds": True},
            )
        )
        alias = f"{self.table_prefix}_" if self.table_prefix else ""
        aliased_name = f"{alias}{self.table.name}.{self.column.name}"
        clause_text = clause_text.replace(
            f"{self.table.name}.{self.column.name}", aliased_name
        )
        dialect_name = self.target_model.Meta.database._backend._dialect.name
        if dialect_name != "sqlite":  # pragma: no cover
            clause_text = clause_text.replace("%%", "%")  # remove %% in some dialects
        clause = text(clause_text)
        return clause
