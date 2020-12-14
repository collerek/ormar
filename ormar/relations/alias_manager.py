import string
import uuid
from random import choices
from typing import Dict, List, TYPE_CHECKING, Type

import sqlalchemy
from sqlalchemy import text

if TYPE_CHECKING:  # pragma: no cover
    from ormar import Model


def get_table_alias() -> str:
    alias = "".join(choices(string.ascii_uppercase, k=2)) + uuid.uuid4().hex[:4]
    return alias.lower()


class AliasManager:
    def __init__(self) -> None:
        self._aliases: Dict[str, str] = dict()
        self._aliases_new: Dict[str, str] = dict()

    @staticmethod
    def prefixed_columns(
        alias: str, table: sqlalchemy.Table, fields: List = None
    ) -> List[text]:
        alias = f"{alias}_" if alias else ""
        all_columns = (
            table.columns
            if not fields
            else [col for col in table.columns if col.name in fields]
        )
        return [
            text(f"{alias}{table.name}.{column.name} as {alias}{column.name}")
            for column in all_columns
        ]

    @staticmethod
    def prefixed_table_name(alias: str, name: str) -> text:
        return text(f"{name} {alias}_{name}")

    def add_relation_type_new(
        self, source_model: Type["Model"], relation_name: str, is_multi: bool = False
    ) -> None:
        parent_key = f"{source_model.get_name()}_{relation_name}"
        if parent_key not in self._aliases_new:
            self._aliases_new[parent_key] = get_table_alias()
        to_field = source_model.Meta.model_fields[relation_name]
        child_model = to_field.to
        related_name = to_field.related_name
        if not related_name:
            related_name = child_model.resolve_relation_name(
                child_model, source_model, explicit_multi=is_multi
            )
        child_key = f"{child_model.get_name()}_{related_name}"
        if child_key not in self._aliases_new:
            self._aliases_new[child_key] = get_table_alias()

    def resolve_relation_join_new(
        self, from_model: Type["Model"], relation_name: str
    ) -> str:
        alias = self._aliases_new.get(f"{from_model.get_name()}_{relation_name}", "")
        return alias
