from typing import List, NamedTuple, TYPE_CHECKING, Tuple, Type

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
    def __init__(
        self,
        used_aliases: List,
        select_from: sqlalchemy.sql.select,
        order_bys: List[sqlalchemy.sql.elements.TextClause],
        columns: List[sqlalchemy.Column],
        fields: List,
    ) -> None:
        self.used_aliases = used_aliases
        self.select_from = select_from
        self.order_bys = order_bys
        self.columns = columns
        self.fields = fields

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
    ) -> Tuple[List, sqlalchemy.sql.select, List, List]:
        for part in item.split("__"):
            if issubclass(
                join_parameters.model_cls.Meta.model_fields[part], ManyToManyField
            ):
                _fields = join_parameters.model_cls.Meta.model_fields
                new_part = _fields[part].to.get_name()
                join_parameters = self._build_join_parameters(
                    part, join_parameters, is_multi=True
                )
                part = new_part
            join_parameters = self._build_join_parameters(part, join_parameters)

        return self.used_aliases, self.select_from, self.columns, self.order_bys

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
        self.order_bys.append(text(f"{alias}_{to_table}.{pkname_alias}"))
        self_related_fields = model_cls.own_table_columns(
            model_cls, self.fields, nested=True,
        )
        self.columns.extend(
            self.relation_manager(model_cls).prefixed_columns(
                alias, model_cls.Meta.table, self_related_fields
            )
        )
        self.used_aliases.append(alias)

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
