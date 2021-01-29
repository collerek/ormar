from collections import OrderedDict
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    TYPE_CHECKING,
    Tuple,
    Type,
    Union,
)

import sqlalchemy
from sqlalchemy import text

from ormar.exceptions import RelationshipInstanceError  # noqa I100
from ormar.fields import BaseField, ManyToManyField  # noqa I100
from ormar.relations import AliasManager

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


class SqlJoin:
    def __init__(  # noqa:  CFQ002
        self,
        used_aliases: List,
        select_from: sqlalchemy.sql.select,
        columns: List[sqlalchemy.Column],
        fields: Optional[Union[Set, Dict]],
        exclude_fields: Optional[Union[Set, Dict]],
        order_columns: Optional[List],
        sorted_orders: OrderedDict,
        main_model: Type["Model"],
        relation_name: str,
        relation_str: str,
        related_models: Any = None,
        own_alias: str = "",
        source_model: Type["Model"] = None,
    ) -> None:
        self.relation_name = relation_name
        self.related_models = related_models or []
        self.select_from = select_from
        self.columns = columns
        self.fields = fields
        self.exclude_fields = exclude_fields
        self.order_columns = order_columns
        self.sorted_orders = sorted_orders
        self.main_model = main_model
        self.own_alias = own_alias
        self.used_aliases = used_aliases
        self.target_field = self.main_model.Meta.model_fields[self.relation_name]

        self._next_model: Optional[Type["Model"]] = None
        self._next_alias: Optional[str] = None

        self.relation_str = relation_str
        self.source_model = source_model

    @property
    def next_model(self) -> Type["Model"]:
        if not self._next_model:  # pragma: nocover
            raise RelationshipInstanceError(
                "Cannot link to related table if relation.to model is not set."
            )
        return self._next_model

    @next_model.setter
    def next_model(self, value: Type["Model"]) -> None:
        self._next_model = value

    @property
    def next_alias(self) -> str:
        if not self._next_alias:  # pragma: nocover
            raise RelationshipInstanceError("Alias for given relation not found.")
        return self._next_alias

    @next_alias.setter
    def next_alias(self, value: str) -> None:
        self._next_alias = value

    @property
    def alias_manager(self) -> AliasManager:
        """
        Shortcut for ormar's model AliasManager stored on Meta.

        :return: alias manager from model's Meta
        :rtype: AliasManager
        """
        return self.main_model.Meta.alias_manager

    def on_clause(self, previous_alias: str, from_clause: str, to_clause: str,) -> text:
        """
        Receives aliases and names of both ends of the join and combines them
        into one text clause used in joins.

        :param previous_alias: alias of previous table
        :type previous_alias: str
        :param from_clause: from table name
        :type from_clause: str
        :param to_clause: to table name
        :type to_clause: str
        :return: clause combining all strings
        :rtype: sqlalchemy.text
        """
        left_part = f"{self.next_alias}_{to_clause}"
        right_part = f"{previous_alias + '_' if previous_alias else ''}{from_clause}"
        return text(f"{left_part}={right_part}")

    def build_join(self) -> Tuple[List, sqlalchemy.sql.select, List, OrderedDict]:
        """
        Main external access point for building a join.
        Splits the join definition, updates fields and exclude_fields if needed,
        handles switching to through models for m2m relations, returns updated lists of
        used_aliases and sort_orders.

        :return: list of used aliases, select from, list of aliased columns, sort orders
        :rtype: Tuple[List[str], Join, List[TextClause], collections.OrderedDict]
        """
        if issubclass(self.target_field, ManyToManyField):
            self.process_m2m_through_table()

        self.next_model = self.target_field.to
        self._forward_join()

        self._process_following_joins()

        return (
            self.used_aliases,
            self.select_from,
            self.columns,
            self.sorted_orders,
        )

    def _forward_join(self) -> None:
        """
        Process actual join.
        Registers complex relation join on encountering of the duplicated alias.
        """
        self.next_alias = self.alias_manager.resolve_relation_alias(
            from_model=self.target_field.owner, relation_name=self.relation_name
        )
        if self.next_alias not in self.used_aliases:
            self._process_join()
        else:
            if "__" in self.relation_str and self.source_model:
                relation_key = f"{self.source_model.get_name()}_{self.relation_str}"
                if relation_key not in self.alias_manager:
                    self.next_alias = self.alias_manager.add_alias(
                        alias_key=relation_key
                    )
                else:
                    self.next_alias = self.alias_manager[relation_key]
                self._process_join()

    def _process_following_joins(self) -> None:
        """
        Iterates through nested models to create subsequent joins.
        """
        for related_name in self.related_models:
            remainder = None
            if (
                isinstance(self.related_models, dict)
                and self.related_models[related_name]
            ):
                remainder = self.related_models[related_name]
            self._process_deeper_join(related_name=related_name, remainder=remainder)

    def _process_deeper_join(self, related_name: str, remainder: Any) -> None:
        """
        Creates nested recurrent instance of SqlJoin for each nested join table,
        updating needed return params here as a side effect.

        Updated are:

        * self.used_aliases,
        * self.select_from,
        * self.columns,
        * self.sorted_orders,

        :param related_name: name of the relation to follow
        :type related_name: str
        :param remainder: deeper tables if there are more nested joins
        :type remainder: Any
        """
        sql_join = SqlJoin(
            used_aliases=self.used_aliases,
            select_from=self.select_from,
            columns=self.columns,
            fields=self.main_model.get_excluded(self.fields, related_name),
            exclude_fields=self.main_model.get_excluded(
                self.exclude_fields, related_name
            ),
            order_columns=self.order_columns,
            sorted_orders=self.sorted_orders,
            main_model=self.next_model,
            relation_name=related_name,
            related_models=remainder,
            relation_str="__".join([self.relation_str, related_name]),
            own_alias=self.next_alias,
            source_model=self.source_model or self.main_model,
        )
        (
            self.used_aliases,
            self.select_from,
            self.columns,
            self.sorted_orders,
        ) = sql_join.build_join()

    def process_m2m_through_table(self) -> None:
        """
        Process Through table of the ManyToMany relation so that source table is
        linked to the through table (one additional join)

        Replaces needed parameters like:

        * self.next_model,
        * self.next_alias,
        * self.relation_name,
        * self.own_alias,
        * self.target_field

        To point to through model
        """
        new_part = self.process_m2m_related_name_change()
        self._replace_many_to_many_order_by_columns(self.relation_name, new_part)

        self.next_model = self.target_field.through
        self._forward_join()

        self.relation_name = new_part
        self.own_alias = self.next_alias
        self.target_field = self.next_model.Meta.model_fields[self.relation_name]

    def process_m2m_related_name_change(self, reverse: bool = False) -> str:
        """
        Extracts relation name to link join through the Through model declared on
        relation field.

        Changes the same names in order_by queries if they are present.

        :param reverse: flag if it's on_clause lookup - use reverse fields
        :type reverse: bool
        :return: new relation name switched to through model field
        :rtype: str
        """
        target_field = self.target_field
        is_primary_self_ref = (
            target_field.self_reference
            and self.relation_name == target_field.self_reference_primary
        )
        if (is_primary_self_ref and not reverse) or (
            not is_primary_self_ref and reverse
        ):
            new_part = target_field.default_source_field_name()  # type: ignore
        else:
            new_part = target_field.default_target_field_name()  # type: ignore
        return new_part

    def _process_join(self,) -> None:  # noqa: CFQ002
        """
        Resolves to and from column names and table names.

        Produces on_clause.

        Performs actual join updating select_from parameter.

        Adds aliases of required column to list of columns to include in query.

        Updates the used aliases list directly.

        Process order_by causes for non m2m relations.

        """
        to_table = self.next_model.Meta.table.name
        to_key, from_key = self.get_to_and_from_keys()

        on_clause = self.on_clause(
            previous_alias=self.own_alias,
            from_clause=f"{self.target_field.owner.Meta.tablename}.{from_key}",
            to_clause=f"{to_table}.{to_key}",
        )
        target_table = self.alias_manager.prefixed_table_name(self.next_alias, to_table)
        self.select_from = sqlalchemy.sql.outerjoin(
            self.select_from, target_table, on_clause
        )

        pkname_alias = self.next_model.get_column_alias(self.next_model.Meta.pkname)
        if not issubclass(self.target_field, ManyToManyField):
            self.get_order_bys(
                to_table=to_table, pkname_alias=pkname_alias,
            )

        self_related_fields = self.next_model.own_table_columns(
            model=self.next_model,
            fields=self.fields,
            exclude_fields=self.exclude_fields,
            use_alias=True,
        )
        self.columns.extend(
            self.alias_manager.prefixed_columns(
                self.next_alias, self.next_model.Meta.table, self_related_fields
            )
        )
        self.used_aliases.append(self.next_alias)

    def _replace_many_to_many_order_by_columns(self, part: str, new_part: str) -> None:
        """
        Substitutes the name of the relation with actual model name in m2m order bys.

        :param part: name of the field with relation
        :type part: str
        :param new_part: name of the target model
        :type new_part: str
        """
        if self.order_columns:
            split_order_columns = [
                x.split("__") for x in self.order_columns if "__" in x
            ]
            for condition in split_order_columns:
                if self._check_if_condition_apply(condition, part):
                    condition[-2] = condition[-2].replace(part, new_part)
            self.order_columns = [x for x in self.order_columns if "__" not in x] + [
                "__".join(x) for x in split_order_columns
            ]

    @staticmethod
    def _check_if_condition_apply(condition: List, part: str) -> bool:
        """
        Checks filter conditions to find if they apply to current join.

        :param condition: list of parts of condition split by '__'
        :type condition: List[str]
        :param part: name of the current relation join.
        :type part: str
        :return: result of the check
        :rtype: bool
        """
        return len(condition) >= 2 and (
            condition[-2] == part or condition[-2][1:] == part
        )

    def set_aliased_order_by(self, condition: List[str], to_table: str,) -> None:
        """
        Substitute hyphens ('-') with descending order.
        Construct actual sqlalchemy text clause using aliased table and column name.

        :param condition: list of parts of a current condition split by '__'
        :type condition: List[str]
        :param to_table: target table
        :type to_table: sqlalchemy.sql.elements.quoted_name
        """
        direction = f"{'desc' if condition[0][0] == '-' else ''}"
        column_alias = self.next_model.get_column_alias(condition[-1])
        order = text(f"{self.next_alias}_{to_table}.{column_alias} {direction}")
        self.sorted_orders["__".join(condition)] = order

    def get_order_bys(self, to_table: str, pkname_alias: str,) -> None:  # noqa: CCR001
        """
        Triggers construction of order bys if they are given.
        Otherwise by default each table is sorted by a primary key column asc.

        :param to_table: target table
        :type to_table: sqlalchemy.sql.elements.quoted_name
        :param pkname_alias: alias of the primary key column
        :type pkname_alias: str
        """
        alias = self.next_alias
        if self.order_columns:
            current_table_sorted = False
            split_order_columns = [
                x.split("__") for x in self.order_columns if "__" in x
            ]
            for condition in split_order_columns:
                if self._check_if_condition_apply(condition, self.relation_name):
                    current_table_sorted = True
                    self.set_aliased_order_by(
                        condition=condition, to_table=to_table,
                    )
            if not current_table_sorted:
                order = text(f"{alias}_{to_table}.{pkname_alias}")
                self.sorted_orders[f"{alias}.{pkname_alias}"] = order

        else:
            order = text(f"{alias}_{to_table}.{pkname_alias}")
            self.sorted_orders[f"{alias}.{pkname_alias}"] = order

    def get_to_and_from_keys(self) -> Tuple[str, str]:
        """
        Based on the relation type, name of the relation and previous models and parts
        stored in JoinParameters it resolves the current to and from keys, which are
        different for ManyToMany relation, ForeignKey and reverse related of relations.

        :return: to key and from key
        :rtype: Tuple[str, str]
        """
        if issubclass(self.target_field, ManyToManyField):
            to_key = self.process_m2m_related_name_change(reverse=True)
            from_key = self.main_model.get_column_alias(self.main_model.Meta.pkname)

        elif self.target_field.virtual:
            to_field = self.target_field.get_related_name()
            to_key = self.target_field.to.get_column_alias(to_field)
            from_key = self.main_model.get_column_alias(self.main_model.Meta.pkname)

        else:
            to_key = self.target_field.to.get_column_alias(
                self.target_field.to.Meta.pkname
            )
            from_key = self.main_model.get_column_alias(self.relation_name)

        return to_key, from_key
