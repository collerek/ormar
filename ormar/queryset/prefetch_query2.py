import abc
from abc import abstractmethod
from typing import (
    Any, Dict,
    List,
    Sequence, Set, TYPE_CHECKING,
    Type, Union, cast,
)

import ormar
from ormar.queryset.clause import QueryClause
from ormar.queryset.query import Query
from ormar.queryset.utils import translate_list_to_dict

if TYPE_CHECKING:  # pragma: no cover
    from ormar import Model, ForeignKeyField
    from ormar.queryset import OrderAction, FilterAction
    from ormar.models.excludable import ExcludableItems


# get dict of models to load
# get dict of already loaded models
# proceed with queries one at a time
# to proceed with query you need to extract corresponding relation fields
# then extract unique values of those fields to use them in where condition
# when loading the next relation
# after all queries are executed you can proceed back and instantiate
# models in current leaf and then populate those models back up


class UniqueList(list):
    def append(self, item: Any) -> None:
        if item not in self:
            super().append(item)


class Task(abc.ABC):

    def __init__(
            self,
            relation_field: "ForeignKeyField",
            parent: "Task"
    ) -> None:
        self.parent = parent
        self.children = []
        if self.parent:
            self.parent.children.append(self)
        self.relation_field = relation_field
        self.table_prefix = ""
        self.rows = []
        self.models = []
        self.use_alias: bool = False

    @property
    def target_name(self) -> str:
        if (
                self.relation_field.self_reference
                and self.relation_field.self_reference_primary == self.relation_field.name
        ):
            return self.relation_field.default_source_field_name()
        else:
            return self.relation_field.default_target_field_name()

    @abstractmethod
    def extract_related_ids(self, column_names: Union[str, List[str]]) -> List:
        pass

    @abstractmethod
    def reload_tree(self):
        pass

    @abstractmethod
    async def load_data(self):
        pass

    def get_filter_for_prefetch(self) -> List["FilterAction"]:
        """
        Populates where clause with condition to return only models within the
        set of extracted ids.
        If there are no ids for relation the empty list is returned.

        :return: list of filter clauses based on original models
        :rtype: List[sqlalchemy.sql.elements.TextClause]
        """
        column_names = self.relation_field.get_model_relation_fields(
            self.parent.use_alias)
        ids = self.parent.extract_related_ids(column_names=column_names)

        if ids:
            return self._prepare_filter_clauses(ids=ids)
        return []

    def _prepare_filter_clauses(self, ids: List) -> List["FilterAction"]:
        clause_target = self.relation_field.get_filter_clause_target()
        filter_column = self.relation_field.get_related_field_name()
        qryclause = QueryClause(
            model_cls=clause_target, select_related=[], filter_clauses=[],
        )
        if isinstance(filter_column, dict):
            kwargs: Dict[str, Union[List, Set]] = dict()
            for own_name, target_name in filter_column.items():
                kwargs[f"{own_name}__in"] = set(x.get(target_name) for x in ids)
        else:
            kwargs = {f"{cast(str, filter_column)}__in": ids}
        filter_clauses, _ = qryclause.prepare_filter(_own_only=False, **kwargs)
        return filter_clauses


class AlreadyLoadedTask(Task):

    def __init__(
            self,
            relation_field: "ForeignKeyField",
            parent: "Task"
    ) -> None:
        super().__init__(
            relation_field=relation_field,
            parent=parent)
        self.use_alias = False
        self._extract_own_models()

    def _extract_own_models(self):
        for model in self.parent.models:
            child_models = getattr(model, self.relation_field.name)
            if isinstance(child_models, list):
                self.models.extend(child_models)
            elif child_models:
                self.models.append(child_models)

    async def load_data(self):
        for child in self.children:
            await child.load_data()

    def reload_tree(self):
        for child in self.children:
            child.reload_tree()

    def extract_related_ids(self, column_names: Union[str, List[str]]) -> List:
        # extract ids from already loaded models
        list_of_ids = UniqueList()
        for model in self.models:
            if isinstance(column_names, list):
                current_id = dict()
                for column in column_names:
                    column = model.get_column_name_from_alias(column)
                    child = getattr(model, column)
                    if isinstance(child, ormar.Model):
                        child = child.pk
                    if isinstance(child, dict):
                        field = model.Meta.model_fields[column]
                        for target_name, own_name in field.names.items():
                            current_id[own_name] = child.get(target_name)
                    else:
                        current_id[model.get_column_alias(column)] = child
                list_of_ids.append(current_id)
            else:
                child = getattr(model, column_names)
                if isinstance(child, ormar.Model):
                    list_of_ids.append(child.pk)
                else:
                    list_of_ids.append(child)
        return list_of_ids


class MasterTask(AlreadyLoadedTask):

    def __init__(self, models):
        self.models = models
        self.use_alias = False
        self.children = []

    def reload_tree(self):
        for child in self.children:
            child.reload_tree()


class LoadTask(Task):

    def __init__(
            self,
            relation_field: "ForeignKeyField",
            excludable: "ExcludableItems",
            orders_by: Dict,
            parent: "Task"
    ) -> None:
        super().__init__(
            relation_field=relation_field,
            parent=parent)
        self.excludable = excludable
        self.exclude_prefix = None
        self.orders_by = orders_by
        self.use_alias = True
        self.grouped_models = dict()

    def reload_tree(self):
        self._instantiate_models()
        self._group_models_by_relation_key()
        for child in self.children:
            child.reload_tree()
        self._populate_parent_models()

    async def load_data(self):
        self._update_excludable_with_related_pks()
        if self.relation_field.is_multi:
            query_target = self.relation_field.through
            select_related = [self.target_name]
        else:
            query_target = self.relation_field.to
            select_related = []

        filter_clauses = self.get_filter_for_prefetch()

        qry = Query(
            model_cls=query_target,
            select_related=select_related,
            filter_clauses=filter_clauses,
            exclude_clauses=[],
            offset=None,
            limit_count=None,
            excludable=self.excludable,
            order_bys=None,
            limit_raw_sql=False,
        )
        expr = qry.build_select_expression()
        print(expr.compile(compile_kwargs={"literal_binds": True}))
        self.rows = await query_target.Meta.database.fetch_all(expr)

        for child in self.children:
            await child.load_data()

    def extract_related_ids(self, column_names: Union[str, List[str]]) -> List:
        # extract ids from raw data
        if not isinstance(column_names, list):
            column_names = [column_names]
        list_of_ids = UniqueList()
        table_prefix = self.table_prefix
        column_names = [
            (f"{table_prefix}_" if table_prefix else "") + column_name
            for column_name in column_names
        ]
        for row in self.rows:
            if all(row[column_name] for column_name in column_names):
                if len(column_names) > 1:
                    list_of_ids.append(
                        {column_name: row[column_name] for column_name in column_names}
                    )
                else:
                    list_of_ids.append(row[column_names[0]])
        return list_of_ids

    def _instantiate_models(self):
        for row in self.rows:
            item = self.relation_field.to.extract_prefixed_table_columns(
                item={}, row=row, table_prefix=self.table_prefix,
                excludable=self.excludable,
            )
            item["__excluded__"] = self.relation_field.to.get_names_to_exclude(
                excludable=self.excludable, alias=self.exclude_prefix
            )
            self.models.append(self.relation_field.to(**item))

    def _group_models_by_relation_key(self):
        relation_keys = self.relation_field.get_related_field_name()
        if not isinstance(relation_keys, list):
            relation_keys = [relation_keys]
        for index, row in enumerate(self.rows):
            key = tuple(
                (row[relation_key]) for relation_key in relation_keys)
            current_group = self.grouped_models.setdefault(key, [])
            current_group.append(self.models[index])
        return self.grouped_models

    def _populate_parent_models(self):
        column_names = self.relation_field.get_model_relation_fields(False)
        if not isinstance(column_names, list):
            column_names = [column_names]
        for model in self.parent.models:
            key = tuple([getattr(model, column_name) for column_name in column_names])
            children = self.grouped_models[key]
            for child in children:
                setattr(model, self.relation_field.name, child)

    def _update_excludable_with_related_pks(self):
        related_field_names = self.relation_field.owner.get_related_field_name(
            target_field=self.relation_field
        )
        alias_manager = self.relation_field.to.Meta.alias_manager
        if self.relation_field.is_multi:
            from_model = self.relation_field.through
            relation_name = self.target_name
        else:
            from_model = self.relation_field.owner
            relation_name = self.relation_field.name
        self.exclude_prefix = alias_manager.resolve_relation_alias(
            from_model=from_model, relation_name=relation_name
        )
        if self.relation_field.is_multi:
            self.table_prefix = self.exclude_prefix
        target_model = self.relation_field.to
        model_excludable = self.excludable.get(model_cls=target_model,
                                               alias=self.exclude_prefix)
        # includes nested pks if not included already
        for related_name in related_field_names:
            if model_excludable.include and not model_excludable.is_included(
                    related_name
            ):
                model_excludable.set_values({related_name}, is_exclude=False)


class PrefetchQuery:
    """
    Query used to fetch related models in subsequent queries.
    Each model is fetched only ones by the name of the relation.
    That means that for each prefetch_related entry next query is issued to database.
    """

    def __init__(  # noqa: CFQ002
            self,
            model_cls: Type["Model"],
            excludable: "ExcludableItems",
            prefetch_related: List,
            select_related: List,
            orders_by: List["OrderAction"],
    ) -> None:
        self.model = model_cls
        self.excludable = excludable
        self.select_dict = translate_list_to_dict(select_related, default={})
        self.prefetch_dict = translate_list_to_dict(prefetch_related, default={})
        self.order_dict = translate_list_to_dict(
            [x.query_str for x in orders_by], is_order=True
        )
        self.load_tasks = []

    async def prefetch_related(
            self, models: Sequence["Model"], rows: List
    ) -> Sequence["Model"]:
        """
        Main entry point for prefetch_query.

        Receives list of already initialized parent models with all children from
        select_related already populated. Receives also list of row sql result rows
        as it's quicker to extract ids that way instead of calling each model.

        Returns list with related models already prefetched and set.

        :param models: list of already instantiated models from main query
        :type models: List[Model]
        :param rows: row sql result of the main query before the prefetch
        :type rows: List[sqlalchemy.engine.result.RowProxy]
        :return: list of models with children prefetched
        :rtype: List[Model]
        """
        parent_task = MasterTask(models=models)
        self._build_load_tree(
            prefetch_dict=self.prefetch_dict,
            select_dict=self.select_dict,
            order_dict=self.order_dict,
            parent=parent_task
        )
        await parent_task.load_data()
        parent_task.reload_tree()
        return parent_task.models

    def _build_load_tree(
            self,
            select_dict: Dict,
            prefetch_dict: Dict,
            order_dict: Dict,
            parent: Task = None,
            model: Type["Model"] = None
    ):
        model = model or self.model
        if not prefetch_dict or prefetch_dict is Ellipsis:
            return
        for related in prefetch_dict.keys():
            if isinstance(select_dict, dict) and related in select_dict:
                task = AlreadyLoadedTask(
                    relation_field=model.Meta.model_fields[related],
                    parent=parent
                )
            else:
                task = LoadTask(
                    relation_field=model.Meta.model_fields[related],
                    excludable=self.excludable,
                    orders_by=order_dict.get(related, {}),
                    parent=parent
                )
            if prefetch_dict and prefetch_dict is not Ellipsis:
                self._build_load_tree(select_dict=select_dict.get(related, {}),
                                      prefetch_dict=prefetch_dict.get(related, {}),
                                      order_dict=order_dict.get(related, {}),
                                      parent=task,
                                      model=model.Meta.model_fields[related].to)
