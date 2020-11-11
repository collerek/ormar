from collections import OrderedDict
from typing import List, NamedTuple, Optional, TYPE_CHECKING, Tuple, Type

import sqlalchemy
from sqlalchemy import text

from ormar.fields import ManyToManyField  # noqa I100
from ormar.relations import AliasManager

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


class JoinParameters(NamedTuple):
    prev_model: Type["Model"]
    previous_alias: str
    from_table: str
    model_cls: Type["Model"]


class SqlJoin:
    def __init__(  # noqa:  CFQ002
        self,
        used_aliases: List,
        select_from: sqlalchemy.sql.select,
        columns: List[sqlalchemy.Column],
        fields: List,
        exclude_fields: List,
        order_columns: Optional[List],
        sorted_orders: OrderedDict,
    ) -> None:
        self.used_aliases = used_aliases
        self.select_from = select_from
        self.columns = columns
        self.fields = fields
        self.exclude_fields = exclude_fields
        self.order_columns = order_columns
        self.sorted_orders = sorted_orders

    @staticmethod
    def relation_manager(model_cls: Type["Model"]) -> AliasManager:
        return model_cls.Meta.alias_manager

    @staticmethod
    def on_clause(
        previous_alias: str, alias: str, from_clause: str, to_clause: str,
    ) -> text:
        left_part = f"{alias}_{to_clause}"
        right_part = f"{previous_alias + '_' if previous_alias else ''}{from_clause}"
        return text(f"{left_part}={right_part}")

    def build_join(
        self, item: str, join_parameters: JoinParameters
    ) -> Tuple[List, sqlalchemy.sql.select, List, OrderedDict]:
        for part in item.split("__"):
            if issubclass(
                join_parameters.model_cls.Meta.model_fields[part], ManyToManyField
            ):
                _fields = join_parameters.model_cls.Meta.model_fields
                new_part = _fields[part].to.get_name()
                self._switch_many_to_many_order_columns(part, new_part)
                join_parameters = self._build_join_parameters(
                    part, join_parameters, is_multi=True
                )
                part = new_part
            join_parameters = self._build_join_parameters(part, join_parameters)

        return (
            self.used_aliases,
            self.select_from,
            self.columns,
            self.sorted_orders,
        )

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
        to_key, from_key = self.get_to_and_from_keys(
            join_params, is_multi, model_cls, part
        )

        on_clause = self.on_clause(
            previous_alias=join_params.previous_alias,
            alias=alias,
            from_clause=f"{join_params.from_table}.{from_key}",
            to_clause=f"{to_table}.{to_key}",
        )
        target_table = self.relation_manager(model_cls).prefixed_table_name(
            alias, to_table
        )
        self.select_from = sqlalchemy.sql.outerjoin(
            self.select_from, target_table, on_clause
        )

        pkname_alias = model_cls.get_column_alias(model_cls.Meta.pkname)
        if not is_multi:
            self.get_order_bys(
                alias=alias,
                to_table=to_table,
                pkname_alias=pkname_alias,
                part=part,
                model_cls=model_cls,
            )

        self_related_fields = model_cls.own_table_columns(
            model_cls, self.fields, self.exclude_fields, nested=True,
        )
        self.columns.extend(
            self.relation_manager(model_cls).prefixed_columns(
                alias, model_cls.Meta.table, self_related_fields
            )
        )
        self.used_aliases.append(alias)

    def _switch_many_to_many_order_columns(self, part: str, new_part: str) -> None:
        if self.order_columns:
            split_order_columns = [
                x.split("__") for x in self.order_columns if "__" in x
            ]
            for condition in split_order_columns:
                if condition[-2] == part or condition[-2][1:] == part:
                    condition[-2] = condition[-2].replace(part, new_part)
            self.order_columns = [x for x in self.order_columns if "__" not in x] + [
                "__".join(x) for x in split_order_columns
            ]

    @staticmethod
    def _check_if_condition_apply(condition: List, part: str) -> bool:
        return len(condition) >= 2 and (
            condition[-2] == part or condition[-2][1:] == part
        )

    def set_aliased_order_by(
        self, condition: List[str], alias: str, to_table: str, model_cls: Type["Model"],
    ) -> None:
        direction = f"{'desc' if condition[0][0] == '-' else ''}"
        column_alias = model_cls.get_column_alias(condition[-1])
        order = text(f"{alias}_{to_table}.{column_alias} {direction}")
        self.sorted_orders["__".join(condition)] = order

    def get_order_bys(  # noqa: CCR001
        self,
        alias: str,
        to_table: str,
        pkname_alias: str,
        part: str,
        model_cls: Type["Model"],
    ) -> None:
        if self.order_columns:
            split_order_columns = [
                x.split("__") for x in self.order_columns if "__" in x
            ]
            for condition in split_order_columns:
                if self._check_if_condition_apply(condition, part):
                    self.set_aliased_order_by(
                        condition=condition,
                        alias=alias,
                        to_table=to_table,
                        model_cls=model_cls,
                    )
        else:
            order = text(f"{alias}_{to_table}.{pkname_alias}")
            self.sorted_orders[f"{to_table}.{pkname_alias}"] = order

    @staticmethod
    def get_to_and_from_keys(
        join_params: JoinParameters,
        is_multi: bool,
        model_cls: Type["Model"],
        part: str,
    ) -> Tuple[str, str]:
        if join_params.prev_model.Meta.model_fields[part].virtual or is_multi:
            to_field = model_cls.resolve_relation_name(
                model_cls, join_params.prev_model
            )
            to_key = model_cls.get_column_alias(to_field)
            from_key = join_params.prev_model.get_column_alias(model_cls.Meta.pkname)
        else:
            to_key = model_cls.get_column_alias(model_cls.Meta.pkname)
            from_key = join_params.prev_model.get_column_alias(part)

        return to_key, from_key
