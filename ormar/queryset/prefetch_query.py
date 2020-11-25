from typing import (
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

from ormar.fields import BaseField, ManyToManyField
from ormar.queryset.clause import QueryClause
from ormar.queryset.query import Query
from ormar.queryset.utils import translate_list_to_dict

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

    @staticmethod
    def _extract_required_ids(
        already_extracted: Dict,
        parent_model: Type["Model"],
        target_model: Type["Model"],
        reverse: bool,
    ) -> Set:
        current_data = already_extracted.get(parent_model.get_name(), {})
        raw_rows = current_data.get("raw", [])
        table_prefix = current_data.get("prefix", "")
        if reverse:
            column_name = parent_model.get_column_alias(parent_model.Meta.pkname)
        else:
            column_name = target_model.resolve_relation_field(
                parent_model, target_model
            ).get_alias()
        list_of_ids = set()
        column_name = (f"{table_prefix}_" if table_prefix else "") + column_name
        for row in raw_rows:
            if row[column_name]:
                list_of_ids.add(row[column_name])
        return list_of_ids

    @staticmethod
    def _get_filter_for_prefetch(
        already_extracted: Dict,
        parent_model: Type["Model"],
        target_model: Type["Model"],
        reverse: bool,
    ) -> List:
        ids = PrefetchQuery._extract_required_ids(
            already_extracted=already_extracted,
            parent_model=parent_model,
            target_model=target_model,
            reverse=reverse,
        )
        if ids:
            qryclause = QueryClause(
                model_cls=target_model, select_related=[], filter_clauses=[],
            )
            if reverse:
                field = target_model.resolve_relation_field(target_model, parent_model)
                if issubclass(field, ManyToManyField):
                    sub_field = target_model.resolve_relation_field(
                        field.through, parent_model
                    )
                    kwargs = {f"{sub_field.get_alias()}__in": ids}
                    qryclause = QueryClause(
                        model_cls=field.through, select_related=[], filter_clauses=[],
                    )

                else:
                    kwargs = {f"{field.get_alias()}__in": ids}
            else:
                target_field = target_model.Meta.model_fields[
                    target_model.Meta.pkname
                ].get_alias()
                kwargs = {f"{target_field}__in": ids}
            filter_clauses, _ = qryclause.filter(**kwargs)
            return filter_clauses
        return []

    @staticmethod
    def _get_model_id_and_field_name(
        target_field: Type["BaseField"], model: "Model"
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        if target_field.virtual:
            is_multi = False
            field_name = model.resolve_relation_name(target_field.to, model)
            model_id = model.pk
        elif issubclass(target_field, ManyToManyField):
            is_multi = True
            field_name = model.resolve_relation_name(target_field.through, model)
            model_id = model.pk
        else:
            is_multi = False
            related_name = model.resolve_relation_name(model, target_field.to)
            related_model = getattr(model, related_name)
            if not related_model:
                return is_multi, None, None
            model_id = related_model.pk
            field_name = target_field.to.Meta.pkname

        return is_multi, field_name, model_id

    @staticmethod
    def _get_group_field_name(
        target_field: Type["BaseField"], model: Type["Model"]
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

    @staticmethod
    def _populate_nested_related(
        model: "Model", already_extracted: Dict, prefetch_dict: Dict
    ) -> "Model":

        related_to_extract = PrefetchQuery._get_names_to_extract(
            prefetch_dict=prefetch_dict, model=model
        )

        for related in related_to_extract:
            target_field = model.Meta.model_fields[related]
            target_model = target_field.to.get_name()
            is_multi, field_name, model_id = PrefetchQuery._get_model_id_and_field_name(
                target_field=target_field, model=model
            )
            if not field_name:
                continue

            children = already_extracted.get(target_model, {}).get(field_name, {})
            for key, child_models in children.items():
                if key == model_id:
                    for child in child_models:
                        setattr(model, related, child)

        return model

    async def prefetch_related(
        self, models: Sequence["Model"], rows: List
    ) -> Sequence["Model"]:
        return await self._prefetch_related_models(models=models, rows=rows)

    async def _prefetch_related_models(
        self, models: Sequence["Model"], rows: List
    ) -> Sequence["Model"]:
        already_extracted = {
            self.model.get_name(): {
                "raw": rows,
                "models": {model.pk: model for model in models},
            }
        }
        select_dict = translate_list_to_dict(self._select_related)
        prefetch_dict = translate_list_to_dict(self._prefetch_related)
        target_model = self.model
        fields = self._columns
        exclude_fields = self._exclude_columns
        for related in prefetch_dict.keys():
            subrelated = await self._extract_related_models(
                related=related,
                target_model=target_model,
                prefetch_dict=prefetch_dict.get(related),
                select_dict=select_dict.get(related),
                already_extracted=already_extracted,
                fields=fields,
                exclude_fields=exclude_fields,
            )
            print(related, subrelated)
        final_models = []
        for model in models:
            final_models.append(
                self._populate_nested_related(
                    model=model,
                    already_extracted=already_extracted,
                    prefetch_dict=prefetch_dict,
                )
            )
        return models

    async def _extract_related_models(  # noqa: CFQ002
        self,
        related: str,
        target_model: Type["Model"],
        prefetch_dict: Dict,
        select_dict: Dict,
        already_extracted: Dict,
        fields: Dict,
        exclude_fields: Dict,
    ) -> None:

        fields = target_model.get_included(fields, related)
        exclude_fields = target_model.get_excluded(exclude_fields, related)
        select_related = []

        target_field = target_model.Meta.model_fields[related]
        reverse = False
        if target_field.virtual or issubclass(target_field, ManyToManyField):
            reverse = True

        parent_model = target_model
        target_model = target_field.to

        filter_clauses = PrefetchQuery._get_filter_for_prefetch(
            already_extracted=already_extracted,
            parent_model=parent_model,
            target_model=target_model,
            reverse=reverse,
        )
        if not filter_clauses:  # related field is empty
            return

        query_target = target_model
        table_prefix = ""
        if issubclass(target_field, ManyToManyField):
            query_target = target_field.through
            select_related = [target_field.to.get_name()]
            table_prefix = target_field.to.Meta.alias_manager.resolve_relation_join(
                from_table=query_target.Meta.tablename,
                to_table=target_field.to.Meta.tablename,
            )
            already_extracted.setdefault(target_model.get_name(), {})[
                "prefix"
            ] = table_prefix

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
        already_extracted.setdefault(target_model.get_name(), {}).update(
            {"raw": rows, "models": {}}
        )

        if prefetch_dict and prefetch_dict is not Ellipsis:
            for subrelated in prefetch_dict.keys():
                submodels = await self._extract_related_models(
                    related=subrelated,
                    target_model=target_model,
                    prefetch_dict=prefetch_dict.get(subrelated),
                    select_dict=select_dict.get(subrelated)
                    if (select_dict and subrelated in select_dict)
                    else {},
                    already_extracted=already_extracted,
                    fields=fields,
                    exclude_fields=exclude_fields,
                )
                print(subrelated, submodels)

        for row in rows:
            field_name = PrefetchQuery._get_group_field_name(
                target_field=target_field, model=parent_model
            )
            print("TEST", field_name, target_model, row[field_name])
            item = target_model.extract_prefixed_table_columns(
                item={},
                row=row,
                table_prefix=table_prefix,
                fields=fields,
                exclude_fields=exclude_fields,
            )
            instance = target_model(**item)
            instance = self._populate_nested_related(
                model=instance,
                already_extracted=already_extracted,
                prefetch_dict=prefetch_dict,
            )
            already_extracted[target_model.get_name()].setdefault(
                field_name, dict()
            ).setdefault(row[field_name], []).append(instance)
            already_extracted[target_model.get_name()]["models"][instance.pk] = instance

        return already_extracted[target_model.get_name()]["models"]
