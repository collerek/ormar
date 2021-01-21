import itertools
from dataclasses import dataclass
from typing import Any, List, TYPE_CHECKING, Tuple, Type

import ormar  # noqa I100
from ormar.queryset.filter_action import FilterAction
from ormar.queryset.utils import get_relationship_alias_model_and_str

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


@dataclass
class Prefix:
    source_model: Type["Model"]
    table_prefix: str
    model_cls: Type["Model"]
    relation_str: str

    @property
    def alias_key(self) -> str:
        source_model_name = self.source_model.get_name()
        return f"{source_model_name}_" f"{self.relation_str}"


class QueryClause:
    """
    Constructs FilterActions from strings passed as arguments
    """

    def __init__(
        self, model_cls: Type["Model"], filter_clauses: List, select_related: List,
    ) -> None:

        self._select_related = select_related[:]
        self.filter_clauses = filter_clauses[:]

        self.model_cls = model_cls
        self.table = self.model_cls.Meta.table

    def prepare_filter(  # noqa: A003
        self, **kwargs: Any
    ) -> Tuple[List[FilterAction], List[str]]:
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
    ) -> Tuple[List[FilterAction], List[str]]:
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
            filter_action = FilterAction(
                filter_str=key, value=value, model_cls=self.model_cls
            )
            select_related = filter_action.update_select_related(
                select_related=select_related
            )

            filter_clauses.append(filter_action)

        self._register_complex_duplicates(select_related)
        filter_clauses = self._switch_filter_action_prefixes(
            filter_clauses=filter_clauses
        )
        return filter_clauses, select_related

    def _register_complex_duplicates(self, select_related: List[str]) -> None:
        """
        Checks if duplicate aliases are presented which can happen in self relation
        or when two joins end with the same pair of models.

        If there are duplicates, the all duplicated joins are registered as source
        model and whole relation key (not just last relation name).

        :param select_related: list of relation strings
        :type select_related: List[str]
        :return: None
        :rtype: None
        """
        prefixes = self._parse_related_prefixes(select_related=select_related)

        manager = self.model_cls.Meta.alias_manager
        filtered_prefixes = sorted(prefixes, key=lambda x: x.table_prefix)
        grouped = itertools.groupby(filtered_prefixes, key=lambda x: x.table_prefix)
        for _, group in grouped:
            sorted_group = sorted(
                group, key=lambda x: len(x.relation_str), reverse=True
            )
            for prefix in sorted_group[:-1]:
                if prefix.alias_key not in manager:
                    manager.add_alias(alias_key=prefix.alias_key)

    def _parse_related_prefixes(self, select_related: List[str]) -> List[Prefix]:
        """
        Walks all relation strings and parses the target models and prefixes.

        :param select_related: list of relation strings
        :type select_related: List[str]
        :return: list of parsed prefixes
        :rtype: List[Prefix]
        """
        prefixes: List[Prefix] = []
        for related in select_related:
            prefix = Prefix(
                self.model_cls,
                *get_relationship_alias_model_and_str(
                    self.model_cls, related.split("__")
                ),
            )
            prefixes.append(prefix)
        return prefixes

    def _switch_filter_action_prefixes(
        self, filter_clauses: List[FilterAction]
    ) -> List[FilterAction]:
        """
        Substitutes aliases for filter action if the complex key (whole relation str) is
        present in alias_manager.

        :param filter_clauses: raw list of actions
        :type filter_clauses: List[FilterAction]
        :return: list of actions with aliases changed if needed
        :rtype: List[FilterAction]
        """
        manager = self.model_cls.Meta.alias_manager
        for action in filter_clauses:
            new_alias = manager.resolve_relation_alias(
                self.model_cls, action.related_str
            )
            if "__" in action.related_str and new_alias:
                action.table_prefix = new_alias
        return filter_clauses
