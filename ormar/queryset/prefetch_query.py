from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    TYPE_CHECKING,
    Tuple,
    Type,
    Union,
)

import ormar
from ormar.fields import BaseField, ManyToManyField
from ormar.queryset.clause import QueryClause
from ormar.queryset.query import Query
from ormar.queryset.utils import extract_models_to_dict_of_lists, translate_list_to_dict

if TYPE_CHECKING:  # pragma: no cover
    from ormar import Model


class PrefetchQuery:
    def __init__(
        self,
        model_cls: Type["Model"],
        fields: Optional[Union[Dict, Set]],
        exclude_fields: Optional[Union[Dict, Set]],
        prefetch_related: List,
        select_related: List,
    ) -> None:

        self.model = model_cls
        self.database = self.model.Meta.database
        self._prefetch_related = prefetch_related
        self._select_related = select_related
        self._exclude_columns = exclude_fields
        self._columns = fields
        self.already_extracted: Dict = dict()
        self.models: Dict = {}
        self.select_dict = translate_list_to_dict(self._select_related)

    async def prefetch_related(
        self, models: Sequence["Model"], rows: List
    ) -> Sequence["Model"]:
        self.models = extract_models_to_dict_of_lists(
            model_type=self.model, models=models, select_dict=self.select_dict
        )
        self.models[self.model.get_name()] = models
        return await self._prefetch_related_models(models=models, rows=rows)

    @staticmethod
    def _get_column_name_for_id_extraction(
        parent_model: Type["Model"],
        target_model: Type["Model"],
        reverse: bool,
        use_raw: bool,
    ) -> str:
        if reverse:
            column_name = parent_model.Meta.pkname
            return (
                parent_model.get_column_alias(column_name) if use_raw else column_name
            )
        else:
            column = target_model.resolve_relation_field(parent_model, target_model)
            return column.get_alias() if use_raw else column.name

    def _extract_ids_from_raw_data(
        self, parent_model: Type["Model"], column_name: str
    ) -> Set:
        list_of_ids = set()
        current_data = self.already_extracted.get(parent_model.get_name(), {})
        table_prefix = current_data.get("prefix", "")
        column_name = (f"{table_prefix}_" if table_prefix else "") + column_name
        for row in current_data.get("raw", []):
            if row[column_name]:
                list_of_ids.add(row[column_name])
        return list_of_ids

    def _extract_ids_from_preloaded_models(
        self, parent_model: Type["Model"], column_name: str
    ) -> Set:
        list_of_ids = set()
        for model in self.models.get(parent_model.get_name(), []):
            child = getattr(model, column_name)
            if isinstance(child, ormar.Model):
                list_of_ids.add(child.pk)
            else:
                list_of_ids.add(child)
        return list_of_ids

    def _extract_required_ids(
        self, parent_model: Type["Model"], target_model: Type["Model"], reverse: bool,
    ) -> Set:

        use_raw = parent_model.get_name() not in self.models

        column_name = self._get_column_name_for_id_extraction(
            parent_model=parent_model,
            target_model=target_model,
            reverse=reverse,
            use_raw=use_raw,
        )

        if use_raw:
            return self._extract_ids_from_raw_data(
                parent_model=parent_model, column_name=column_name
            )

        return self._extract_ids_from_preloaded_models(
            parent_model=parent_model, column_name=column_name
        )

    @staticmethod
    def _get_clause_target_and_filter_column_name(
        parent_model: Type["Model"], target_model: Type["Model"], reverse: bool
    ) -> Tuple[Type["Model"], str]:
        if reverse:
            field = target_model.resolve_relation_field(target_model, parent_model)
            if issubclass(field, ManyToManyField):
                sub_field = target_model.resolve_relation_field(
                    field.through, parent_model
                )
                return field.through, sub_field.get_alias()
            else:
                return target_model, field.get_alias()
        target_field = target_model.get_column_alias(target_model.Meta.pkname)
        return target_model, target_field

    def _get_filter_for_prefetch(
        self, parent_model: Type["Model"], target_model: Type["Model"], reverse: bool,
    ) -> List:
        ids = self._extract_required_ids(
            parent_model=parent_model, target_model=target_model, reverse=reverse,
        )
        if ids:
            (
                clause_target,
                filter_column,
            ) = self._get_clause_target_and_filter_column_name(
                parent_model=parent_model, target_model=target_model, reverse=reverse
            )
            qryclause = QueryClause(
                model_cls=clause_target, select_related=[], filter_clauses=[],
            )
            kwargs = {f"{filter_column}__in": ids}
            filter_clauses, _ = qryclause.filter(**kwargs)
            return filter_clauses
        return []

    @staticmethod
    def _get_model_id(target_field: Type["BaseField"], model: "Model") -> Optional[int]:
        if target_field.virtual or issubclass(target_field, ManyToManyField):
            return model.pk
        related_name = model.resolve_relation_name(model, target_field.to)
        related_model = getattr(model, related_name)
        return None if not related_model else related_model.pk

    @staticmethod
    def _get_related_field_name(
        target_field: Type["BaseField"], model: Union["Model", Type["Model"]]
    ) -> str:
        if issubclass(target_field, ManyToManyField):
            return model.resolve_relation_name(target_field.through, model)
        if target_field.virtual:
            return model.resolve_relation_name(target_field.to, model)
        return target_field.to.Meta.pkname

    @staticmethod
    def _get_names_to_extract(prefetch_dict: Dict, model: "Model") -> List:
        related_to_extract = []
        if prefetch_dict and prefetch_dict is not Ellipsis:
            related_to_extract = [
                related
                for related in model.extract_related_names()
                if related in prefetch_dict
            ]
        return related_to_extract

    def _populate_nested_related(self, model: "Model", prefetch_dict: Dict) -> "Model":

        related_to_extract = self._get_names_to_extract(
            prefetch_dict=prefetch_dict, model=model
        )

        for related in related_to_extract:
            target_field = model.Meta.model_fields[related]
            target_model = target_field.to.get_name()
            model_id = self._get_model_id(target_field=target_field, model=model)

            if model_id is None:  # pragma: no cover
                continue

            field_name = self._get_related_field_name(
                target_field=target_field, model=model
            )

            children = self.already_extracted.get(target_model, {}).get(field_name, {})
            self._set_children_on_model(
                model=model, related=related, children=children, model_id=model_id
            )

        return model

    @staticmethod
    def _set_children_on_model(
        model: "Model", related: str, children: Dict, model_id: int
    ) -> None:
        for key, child_models in children.items():
            if key == model_id:
                for child in child_models:
                    setattr(model, related, child)

    async def _prefetch_related_models(
        self, models: Sequence["Model"], rows: List
    ) -> Sequence["Model"]:
        self.already_extracted = {self.model.get_name(): {"raw": rows}}
        select_dict = translate_list_to_dict(self._select_related)
        prefetch_dict = translate_list_to_dict(self._prefetch_related)
        target_model = self.model
        fields = self._columns
        exclude_fields = self._exclude_columns
        for related in prefetch_dict.keys():
            await self._extract_related_models(
                related=related,
                target_model=target_model,
                prefetch_dict=prefetch_dict.get(related, {}),
                select_dict=select_dict.get(related, {}),
                fields=fields,
                exclude_fields=exclude_fields,
            )
        final_models = []
        for model in models:
            final_models.append(
                self._populate_nested_related(model=model, prefetch_dict=prefetch_dict,)
            )
        return models

    async def _extract_related_models(  # noqa: CFQ002, CCR001
        self,
        related: str,
        target_model: Type["Model"],
        prefetch_dict: Dict,
        select_dict: Dict,
        fields: Union[Set[Any], Dict[Any, Any], None],
        exclude_fields: Union[Set[Any], Dict[Any, Any], None],
    ) -> None:

        fields = target_model.get_included(fields, related)
        exclude_fields = target_model.get_excluded(exclude_fields, related)
        target_field = target_model.Meta.model_fields[related]
        reverse = False
        if target_field.virtual or issubclass(target_field, ManyToManyField):
            reverse = True

        parent_model = target_model

        filter_clauses = self._get_filter_for_prefetch(
            parent_model=parent_model, target_model=target_field.to, reverse=reverse,
        )
        if not filter_clauses:  # related field is empty
            return

        already_loaded = select_dict is Ellipsis or related in select_dict

        if not already_loaded:
            # If not already loaded with select_related
            table_prefix, rows = await self._run_prefetch_query(
                target_field=target_field,
                fields=fields,
                exclude_fields=exclude_fields,
                filter_clauses=filter_clauses,
            )
        else:
            rows = []
            table_prefix = ""

        if prefetch_dict and prefetch_dict is not Ellipsis:
            for subrelated in prefetch_dict.keys():
                await self._extract_related_models(
                    related=subrelated,
                    target_model=target_field.to,
                    prefetch_dict=prefetch_dict.get(subrelated, {}),
                    select_dict=self._get_select_related_if_apply(
                        subrelated, select_dict
                    ),
                    fields=fields,
                    exclude_fields=exclude_fields,
                )

        if not already_loaded:
            self._populate_rows(
                rows=rows,
                parent_model=parent_model,
                target_field=target_field,
                table_prefix=table_prefix,
                fields=fields,
                exclude_fields=exclude_fields,
                prefetch_dict=prefetch_dict,
            )
        else:
            self._update_already_loaded_rows(
                target_field=target_field, prefetch_dict=prefetch_dict,
            )

    async def _run_prefetch_query(
        self,
        target_field: Type["BaseField"],
        fields: Union[Set[Any], Dict[Any, Any], None],
        exclude_fields: Union[Set[Any], Dict[Any, Any], None],
        filter_clauses: List,
    ) -> Tuple[str, List]:
        target_model = target_field.to
        target_name = target_model.get_name()
        select_related = []
        query_target = target_model
        table_prefix = ""
        if issubclass(target_field, ManyToManyField):
            query_target = target_field.through
            select_related = [target_name]
            table_prefix = target_field.to.Meta.alias_manager.resolve_relation_join(
                from_table=query_target.Meta.tablename,
                to_table=target_field.to.Meta.tablename,
            )
            self.already_extracted.setdefault(target_name, {})["prefix"] = table_prefix

        qry = Query(
            model_cls=query_target,
            select_related=select_related,
            filter_clauses=filter_clauses,
            exclude_clauses=[],
            offset=None,
            limit_count=None,
            fields=fields,
            exclude_fields=exclude_fields,
            order_bys=None,
        )
        expr = qry.build_select_expression()
        # print(expr.compile(compile_kwargs={"literal_binds": True}))
        rows = await self.database.fetch_all(expr)
        self.already_extracted.setdefault(target_name, {}).update({"raw": rows})
        return table_prefix, rows

    @staticmethod
    def _get_select_related_if_apply(related: str, select_dict: Dict) -> Dict:
        return (
            select_dict.get(related, {})
            if (select_dict and select_dict is not Ellipsis and related in select_dict)
            else {}
        )

    def _update_already_loaded_rows(  # noqa: CFQ002
        self, target_field: Type["BaseField"], prefetch_dict: Dict,
    ) -> None:
        target_model = target_field.to
        for instance in self.models.get(target_model.get_name(), []):
            self._populate_nested_related(
                model=instance, prefetch_dict=prefetch_dict,
            )

    def _populate_rows(  # noqa: CFQ002
        self,
        rows: List,
        target_field: Type["BaseField"],
        parent_model: Type["Model"],
        table_prefix: str,
        fields: Union[Set[Any], Dict[Any, Any], None],
        exclude_fields: Union[Set[Any], Dict[Any, Any], None],
        prefetch_dict: Dict,
    ) -> None:
        target_model = target_field.to
        for row in rows:
            field_name = self._get_related_field_name(
                target_field=target_field, model=parent_model
            )
            item = target_model.extract_prefixed_table_columns(
                item={},
                row=row,
                table_prefix=table_prefix,
                fields=fields,
                exclude_fields=exclude_fields,
            )
            instance = target_model(**item)
            instance = self._populate_nested_related(
                model=instance, prefetch_dict=prefetch_dict,
            )
            field_db_name = target_model.get_column_alias(field_name)
            self.already_extracted[target_model.get_name()].setdefault(
                field_name, dict()
            ).setdefault(row[field_db_name], []).append(instance)
