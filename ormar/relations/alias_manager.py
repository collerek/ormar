import string
import uuid
from random import choices
from typing import Any, Dict, List, TYPE_CHECKING, Type, Union
from collections import defaultdict

import sqlalchemy
from sqlalchemy import text

if TYPE_CHECKING:  # pragma: no cover
    from ormar import Model
    from ormar.models import ModelRow
    from ormar.fields import ForeignKeyField


def get_table_alias() -> str:
    """
    Creates a random string that is used to alias tables in joins.
    It's necessary that each relation has it's own aliases cause you can link
    to the same target tables from multiple fields on one model as well as from
    multiple different models in one join.

    :return: randomly generated alias
    :rtype: str
    """
    alias = "".join(choices(string.ascii_uppercase, k=2)) + uuid.uuid4().hex[:4]
    return alias.lower()


class AliasManager:
    """
    Keep all aliases of relations between different tables.
    One global instance is shared between all models.
    """

    def __init__(self) -> None:
        self._reversed_aliases: Dict[str, str] = dict()
        self._relation_aliases: Dict[str, str] = defaultdict(get_table_alias)

    def __contains__(self, item: str) -> bool:
        return self._relation_aliases.__contains__(item)

    def __getitem__(self, key: str) -> Any:
        return self._relation_aliases.__getitem__(key)

    @property
    def reversed_aliases(self) -> Dict:
        """
        Returns swapped key-value pairs from aliases where alias is the key.

        :return: dictionary of prefix to relation
        :rtype: Dict
        """
        reversed_aliases = {v: k for k, v in self._relation_aliases.items()}
        self._reversed_aliases = reversed_aliases
        return self._reversed_aliases

    @staticmethod
    def prefixed_columns(
        alias: str, table: sqlalchemy.Table, fields: List = None
    ) -> List[text]:
        """
        Creates a list of aliases sqlalchemy text clauses from
        string alias and sqlalchemy.Table.

        Optional list of fields to include can be passed to extract only those columns.
        List has to have sqlalchemy names of columns (ormar aliases) not the ormar ones.

        :param alias: alias of given table
        :type alias: str
        :param table: table from which fields should be aliased
        :type table: sqlalchemy.Table
        :param fields: fields to include
        :type fields: Optional[List[str]]
        :return: list of sqlalchemy text clauses with "column name as aliased name"
        :rtype: List[text]
        """
        alias = f"{alias}_" if alias else ""
        all_columns = (
            table.columns
            if not fields
            else [col for col in table.columns if col.name in fields]
        )
        return [column.label(f"{alias}{column.name}") for column in all_columns]

    @staticmethod
    def prefixed_table_name(alias: str, table: sqlalchemy.Table) -> text:
        """
        Creates text clause with table name with aliased name.

        :param alias: alias of given table
        :type alias: str
        :param table: table
        :type table: sqlalchemy.Table
        :return: sqlalchemy text clause as "table_name aliased_name"
        :rtype: sqlalchemy text clause
        """
        return table.alias(f"{alias}_{table.name}")

    def resolve_relation_string_alias(
        self, source_model: Union[Type["Model"], Type["ModelRow"]], relation_string: str
    ) -> str:
        """
        Given source model and relation string returns the alias for this complex
        relation if it exists, otherwise fallback to normal relation from a relation
        field definition.

        :param source_model: model with query starts
        :type source_model: source Model
        :param relation_string: string with relation joins defined
        :type relation_string: str
        :return: alias of the relation
        :rtype: str
        """
        return self._relation_aliases[f"{source_model.get_name()}_{relation_string}"]
