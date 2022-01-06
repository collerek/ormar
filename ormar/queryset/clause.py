import itertools
from dataclasses import dataclass
from enum import Enum
from typing import Any, Generator, List, TYPE_CHECKING, Tuple, Type

import sqlalchemy

import ormar  # noqa I100
from ormar.queryset.actions.filter_action import FilterAction
from ormar.queryset.utils import get_relationship_alias_model_and_str

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


class FilterType(Enum):
    AND = 1
    OR = 2


class FilterGroup:
    """
    Filter groups are used in complex queries condition to group and and or
    clauses in where condition
    """

    def __init__(
        self,
        *args: Any,
        _filter_type: FilterType = FilterType.AND,
        _exclude: bool = False,
        **kwargs: Any,
    ) -> None:
        self.filter_type = _filter_type
        self.exclude = _exclude
        self._nested_groups: List["FilterGroup"] = list(args)
        self._resolved = False
        self.is_source_model_filter = False
        self._kwargs_dict = kwargs
        self.actions: List[FilterAction] = []

    def __and__(self, other: "FilterGroup") -> "FilterGroup":
        return FilterGroup(self, other)

    def __or__(self, other: "FilterGroup") -> "FilterGroup":
        return FilterGroup(self, other, _filter_type=FilterType.OR)

    def __invert__(self) -> "FilterGroup":
        self.exclude = not self.exclude
        return self

    def resolve(
        self,
        model_cls: Type["Model"],
        select_related: List = None,
        filter_clauses: List = None,
    ) -> Tuple[List[FilterAction], List[str]]:
        """
        Resolves the FilterGroups actions to use proper target model, replace
        complex relation prefixes if needed and nested groups also resolved.

        :param model_cls: model from which the query is run
        :type model_cls: Type["Model"]
        :param select_related: list of models to join
        :type select_related: List[str]
        :param filter_clauses: list of filter conditions
        :type filter_clauses: List[FilterAction]
        :return: list of filter conditions and select_related list
        :rtype: Tuple[List[FilterAction], List[str]]
        """
        select_related = select_related if select_related is not None else []
        filter_clauses = filter_clauses if filter_clauses is not None else []
        qryclause = QueryClause(
            model_cls=model_cls,
            select_related=select_related,
            filter_clauses=filter_clauses,
        )
        own_filter_clauses, select_related = qryclause.prepare_filter(
            _own_only=True, **self._kwargs_dict
        )
        self.actions = own_filter_clauses
        filter_clauses = filter_clauses + own_filter_clauses
        self._resolved = True
        if self._nested_groups:
            for group in self._nested_groups:
                (filter_clauses, select_related) = group.resolve(
                    model_cls=model_cls,
                    select_related=select_related,
                    filter_clauses=filter_clauses,
                )
        return filter_clauses, select_related

    def _iter(self) -> Generator:
        """
        Iterates all actions in a tree
        :return: generator yielding from own actions and nested groups
        :rtype: Generator
        """
        for group in self._nested_groups:
            yield from group._iter()
        yield from self.actions

    def _get_text_clauses(self) -> List[sqlalchemy.sql.expression.TextClause]:
        """
        Helper to return list of text queries from actions and nested groups
        :return: list of text queries from actions and nested groups
        :rtype: List[sqlalchemy.sql.elements.TextClause]
        """
        return [x.get_text_clause() for x in self._nested_groups] + [
            x.get_text_clause() for x in self.actions
        ]

    def get_text_clause(self) -> sqlalchemy.sql.expression.TextClause:
        """
        Returns all own actions and nested groups conditions compiled and joined
        inside parentheses.
        Escapes characters if it's required.
        Substitutes values of the models if value is a ormar Model with its pk value.
        Compiles the clause.

        :return: complied and escaped clause
        :rtype: sqlalchemy.sql.elements.TextClause
        """
        if self.filter_type == FilterType.AND:
            clause = sqlalchemy.sql.and_(*self._get_text_clauses()).self_group()
        else:
            clause = sqlalchemy.sql.or_(*self._get_text_clauses()).self_group()
        if self.exclude:
            clause = sqlalchemy.sql.not_(clause)
        return clause


def or_(*args: FilterGroup, **kwargs: Any) -> FilterGroup:
    """
    Construct or filter from nested groups and keyword arguments

    :param args: nested filter groups
    :type args: Tuple[FilterGroup]
    :param kwargs: fields names and proper value types
    :type kwargs: Any
    :return: FilterGroup ready to be resolved
    :rtype: ormar.queryset.clause.FilterGroup
    """
    return FilterGroup(_filter_type=FilterType.OR, *args, **kwargs)


def and_(*args: FilterGroup, **kwargs: Any) -> FilterGroup:
    """
    Construct and filter from nested groups and keyword arguments

    :param args: nested filter groups
    :type args: Tuple[FilterGroup]
    :param kwargs: fields names and proper value types
    :type kwargs: Any
    :return: FilterGroup ready to be resolved
    :rtype: ormar.queryset.clause.FilterGroup
    """
    return FilterGroup(_filter_type=FilterType.AND, *args, **kwargs)


@dataclass
class Prefix:
    source_model: Type["Model"]
    table_prefix: str
    model_cls: Type["Model"]
    relation_str: str
    is_through: bool

    @property
    def alias_key(self) -> str:
        source_model_name = self.source_model.get_name()
        return f"{source_model_name}_" f"{self.relation_str}"


class QueryClause:
    """
    Constructs FilterActions from strings passed as arguments
    """

    def __init__(
        self, model_cls: Type["Model"], filter_clauses: List, select_related: List
    ) -> None:

        self._select_related = select_related[:]
        self.filter_clauses = filter_clauses[:]

        self.model_cls = model_cls
        self.table = self.model_cls.Meta.table

    def prepare_filter(  # noqa: A003
        self, _own_only: bool = False, **kwargs: Any
    ) -> Tuple[List[FilterAction], List[str]]:
        """
        Main external access point that processes the clauses into sqlalchemy text
        clauses and updates select_related list with implicit related tables
        mentioned in select_related strings but not included in select_related.

        :param _own_only:
        :type _own_only:
        :param kwargs: key, value pair with column names and values
        :type kwargs: Any
        :return: Tuple with list of where clauses and updated select_related list
        :rtype: Tuple[List[sqlalchemy.sql.elements.TextClause], List[str]]
        """
        if kwargs.get("pk"):
            pk_name = self.model_cls.get_column_alias(self.model_cls.Meta.pkname)
            kwargs[pk_name] = kwargs.pop("pk")

        filter_clauses, select_related = self._populate_filter_clauses(
            _own_only=_own_only, **kwargs
        )

        return filter_clauses, select_related

    def _populate_filter_clauses(
        self, _own_only: bool, **kwargs: Any
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
        own_filter_clauses = []
        select_related = list(self._select_related)

        for key, value in kwargs.items():
            filter_action = FilterAction(
                filter_str=key, value=value, model_cls=self.model_cls
            )
            select_related = filter_action.update_select_related(
                select_related=select_related
            )

            own_filter_clauses.append(filter_action)

        self._register_complex_duplicates(select_related)
        filter_clauses = self._switch_filter_action_prefixes(
            filter_clauses=filter_clauses + own_filter_clauses
        )
        if _own_only:
            return own_filter_clauses, select_related
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

        for action in filter_clauses:
            if isinstance(action, FilterGroup):
                for action2 in action._iter():
                    self._verify_prefix_and_switch(action2)
            else:
                self._verify_prefix_and_switch(action)
        return filter_clauses

    def _verify_prefix_and_switch(self, action: "FilterAction") -> None:
        """
        Helper to switch prefix to complex relation one if required
        :param action: action to switch prefix in
        :type action: ormar.queryset.actions.filter_action.FilterAction
        """
        manager = self.model_cls.Meta.alias_manager
        new_alias = manager.resolve_relation_alias(self.model_cls, action.related_str)
        if "__" in action.related_str and new_alias:
            action.table_prefix = new_alias
