from typing import TYPE_CHECKING, Type

import sqlalchemy
from sqlalchemy import text

from ormar.queryset.actions.query_action import QueryAction  # noqa: I100, I202

if TYPE_CHECKING:  # pragma: nocover
    from ormar import Model


class OrderAction(QueryAction):
    """
    Order Actions is populated by queryset when order_by() is called.

    All required params are extracted but kept raw until actual filter clause value
    is required -> then the action is converted into text() clause.

    Extracted in order to easily change table prefixes on complex relations.
    """

    def __init__(
        self, order_str: str, model_cls: Type["Model"], alias: str = None
    ) -> None:
        self.direction: str = ""
        super().__init__(query_str=order_str, model_cls=model_cls)
        self.is_source_model_order = False
        if alias:
            self.table_prefix = alias
        if self.source_model == self.target_model and "__" not in self.related_str:
            self.is_source_model_order = True

    @property
    def field_alias(self) -> str:
        return self.target_model.get_column_alias(self.field_name)

    def get_field_name_text(self) -> str:
        """
        Escapes characters if it's required.
        Substitutes values of the models if value is a ormar Model with its pk value.
        Compiles the clause.

        :return: complied and escaped clause
        :rtype: sqlalchemy.sql.elements.TextClause
        """
        prefix = f"{self.table_prefix}_" if self.table_prefix else ""
        return f"{prefix}{self.table}" f".{self.field_alias}"

    def get_min_or_max(self) -> sqlalchemy.sql.expression.TextClause:
        """
        Used in limit sub queries where you need to use aggregated functions
        in order to order by columns not included in group by.

        :return: min or max function to order
        :rtype: sqlalchemy.sql.elements.TextClause
        """
        prefix = f"{self.table_prefix}_" if self.table_prefix else ""
        if self.direction == "":
            return text(f"min({prefix}{self.table}" f".{self.field_alias})")
        return text(f"max({prefix}{self.table}" f".{self.field_alias}) desc")

    def get_text_clause(self) -> sqlalchemy.sql.expression.TextClause:
        """
        Escapes characters if it's required.
        Substitutes values of the models if value is a ormar Model with its pk value.
        Compiles the clause.

        :return: complied and escaped clause
        :rtype: sqlalchemy.sql.elements.TextClause
        """
        prefix = f"{self.table_prefix}_" if self.table_prefix else ""
        table_name = self.table.name
        field_name = self.field_alias
        if not prefix:
            dialect = self.target_model.Meta.database._backend._dialect
            table_name = dialect.identifier_preparer.quote(table_name)
            field_name = dialect.identifier_preparer.quote(field_name)
        return text(f"{prefix}{table_name}" f".{field_name} {self.direction}")

    def _split_value_into_parts(self, order_str: str) -> None:
        if order_str.startswith("-"):
            self.direction = "desc"
            order_str = order_str[1:]
        parts = order_str.split("__")
        self.field_name = parts[-1]
        self.related_parts = parts[:-1]

    def check_if_filter_apply(self, target_model: Type["Model"], alias: str) -> bool:
        """
        Checks filter conditions to find if they apply to current join.

        :param target_model: model which is now processed
        :type target_model: Type["Model"]
        :param alias: prefix of the relation
        :type alias: str
        :return: result of the check
        :rtype: bool
        """
        return target_model == self.target_model and alias == self.table_prefix
