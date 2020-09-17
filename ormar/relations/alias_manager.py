import string
import uuid
from random import choices
from typing import List

import sqlalchemy
from sqlalchemy import text


def get_table_alias() -> str:
    alias = "".join(choices(string.ascii_uppercase, k=2)) + uuid.uuid4().hex[:4]
    return alias.lower()


class AliasManager:
    def __init__(self) -> None:
        self._aliases = dict()

    @staticmethod
    def prefixed_columns(alias: str, table: sqlalchemy.Table) -> List[text]:
        return [
            text(f"{alias}_{table.name}.{column.name} as {alias}_{column.name}")
            for column in table.columns
        ]

    @staticmethod
    def prefixed_table_name(alias: str, name: str) -> text:
        return text(f"{name} {alias}_{name}")

    def add_relation_type(self, to_table_name: str, table_name: str,) -> None:
        if f"{table_name}_{to_table_name}" not in self._aliases:
            self._aliases[f"{table_name}_{to_table_name}"] = get_table_alias()
        if f"{to_table_name}_{table_name}" not in self._aliases:
            self._aliases[f"{to_table_name}_{table_name}"] = get_table_alias()

    def resolve_relation_join(self, from_table: str, to_table: str) -> str:
        return self._aliases.get(f"{from_table}_{to_table}", "")
