from typing import Optional, TYPE_CHECKING, Type

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
        self,
        order_str: str,
        model_cls: Type["Model"],
        alias: str = None,
        nulls_last: Optional[bool] = None,
        nulls_first: Optional[bool] = None,
    ) -> None:

        self.direction: str = ""
        super().__init__(query_str=order_str, model_cls=model_cls)
        self.is_source_model_order = False
        if alias:
            self.table_prefix = alias
        if self.source_model == self.target_model and "__" not in self.related_str:
            self.is_source_model_order = True

        self.nulls = self._get_nulls(nulls_last=nulls_last, nulls_first=nulls_first)

    @property
    def field_alias(self) -> str:
        return self.target_model.get_column_alias(self.field_name)

    @property
    def is_mysql_bool(self) -> bool:
        return self.target_model.Meta.database._backend._dialect.name == "mysql"

    @property
    def is_postgres_bool(self) -> bool:
        dialect = self.target_model.Meta.database._backend._dialect.name
        field_type = self.target_model.Meta.model_fields[self.field_name].__type__
        return dialect == "postgresql" and field_type == bool

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
        in order to order by columns not included in group by. For postgres bool
        field it's using bool_or function as aggregates does not work with this type
        of columns.

        :return: min or max function to order
        :rtype: sqlalchemy.sql.elements.TextClause
        """
        prefix = f"{self.table_prefix}_" if self.table_prefix else ""
        if self.direction == "":
            function = "min" if not self.is_postgres_bool else "bool_or"
            return text(f"{function}({prefix}{self.table}" f".{self.field_alias})")
        function = "max" if not self.is_postgres_bool else "bool_or"
        return text(f"{function}({prefix}{self.table}" f".{self.field_alias}) desc")

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

        return text(
            f"{prefix}{table_name}"
            f".{self._get_field_name_direction_nulls(field_name=field_name)}"
        )

    def _split_value_into_parts(self, order_str: str) -> None:
        if order_str.startswith("-"):
            self.direction = "desc"
            order_str = order_str[1:]
        parts = order_str.split("__")
        self.field_name = parts[-1]
        self.related_parts = parts[:-1]

    @staticmethod
    def _get_nulls(
        nulls_last: Optional[bool] = None,
        nulls_first: Optional[bool] = None,
    ) -> Optional[str]:
        """
        Returned `FIRST` or `LAST` string for condition on nulls value

        :param nulls_last: optional boolean flag to Produce the `NULLS LAST`
        :type nulls_last: Optional[bool]
        :param nulls_first: optional boolean flag to Produce the `NULLS FIRST`
        :type nulls_first: Optional[bool]
        :return: result of the nulls last of nulls first or none
        :rtype: Optional[str]
        """

        if nulls_first or (not nulls_last and nulls_last is not None):
            return "first"

        if nulls_last or (not nulls_first and nulls_first is not None):
            return "last"

        return None

    def _handle_field_nulls_mysql(self, field_name: str, result: str) -> str:
        """
        Generate the Final Query with handling mysql syntax for nulls value

        :param field_name: string name of this field for order
        :type field_name: str
        :param result: query generated in previous stage without nulls value
        :type result: str
        :return: result of the final query by field name and direction and nulls value
        :rtype: str
        """

        if not self.is_mysql_bool:
            return result + f" nulls {self.nulls}"  # pragma: no cover

        condition: str = "not" if self.nulls == "first" else ""  # pragma: no cover
        return f"{field_name} is {condition} null, {result}"  # pragma: no cover

    def _get_field_name_direction_nulls(self, field_name: str) -> str:
        """
        Generate the Query of Order for this field name by direction and nulls value

        :param field_name: string name of this field for order
        :type field_name: str
        :return: result of the query by field name and direction and nulls value
        :rtype: str
        """

        result: str = f"{field_name} {self.direction}"
        if self.nulls is not None:
            return self._handle_field_nulls_mysql(field_name=field_name, result=result)

        return result

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
