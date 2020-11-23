from typing import Dict, List, Optional, Sequence, Set, TYPE_CHECKING, Type, Union

import ormar
from ormar.fields import ManyToManyField
from ormar.queryset.clause import QueryClause
from ormar.queryset.query import Query

if TYPE_CHECKING:  # pragma: no cover
    from ormar import Model


class PrefetchQuery:

    def __init__(self,
                 model_cls: Type["Model"],
                 fields: Optional[Union[Dict, Set]],
                 exclude_fields: Optional[Union[Dict, Set]],
                 prefetch_related: List
                 ):

        self.model = model_cls
        self.database = self.model.Meta.database
        self._prefetch_related = prefetch_related
        self._exclude_columns = exclude_fields
        self._columns = fields

    @staticmethod
    def _extract_required_ids(already_extracted: Dict,
                              parent_model: Type["Model"],
                              target_model: Type["Model"],
                              reverse: bool) -> Set:
        raw_rows = already_extracted.get(parent_model.get_name(), {}).get('raw', [])
        if reverse:
            column_name = parent_model.get_column_alias(parent_model.Meta.pkname)
        else:
            column_name = target_model.resolve_relation_field(parent_model, target_model).get_alias()
        list_of_ids = set()
        for row in raw_rows:
            if row[column_name]:
                list_of_ids.add(row[column_name])
        return list_of_ids

    @staticmethod
    def _get_filter_for_prefetch(already_extracted: Dict,
                                 parent_model: Type["Model"],
                                 target_model: Type["Model"],
                                 reverse: bool) -> List:
        ids = PrefetchQuery._extract_required_ids(already_extracted=already_extracted,
                                                  parent_model=parent_model,
                                                  target_model=target_model,
                                                  reverse=reverse)
        if ids:
            qryclause = QueryClause(
                model_cls=target_model,
                select_related=[],
                filter_clauses=[],
            )
            if reverse:
                field = target_model.resolve_relation_field(target_model, parent_model)
                if issubclass(field, ManyToManyField):
                    sub_field = target_model.resolve_relation_field(field.through, parent_model)
                    kwargs = {f'{sub_field.get_alias()}__in': ids}
                    qryclause = QueryClause(
                        model_cls=field.through,
                        select_related=[],
                        filter_clauses=[],
                    )

                else:
                    kwargs = {f'{field.get_alias()}__in': ids}
            else:
                target_field = target_model.Meta.model_fields[target_model.Meta.pkname].get_alias()
                kwargs = {f'{target_field}__in': ids}
            filter_clauses, _ = qryclause.filter(**kwargs)
            return filter_clauses
        return []

    @staticmethod
    def _populate_nested_related(model: "Model",
                                 already_extracted: Dict) -> "Model":

        for related in model.extract_related_names():
            reverse = False

            target_field = model.Meta.model_fields[related]
            target_model = target_field.to.get_name()
            if target_field.virtual:
                reverse = True
                field_name = model.resolve_relation_name(target_field.to, model)
                model_id = model.pk
            elif issubclass(target_field, ManyToManyField):
                reverse = True
                field_name = model.resolve_relation_name(target_field.through, model)
                model_id = model.pk
            else:
                related_name = model.resolve_relation_name(model, target_field.to)
                related_model = getattr(model, related_name)
                if not related_model:
                    continue
                model_id = related_model.pk
                field_name = target_field.to.Meta.pkname

            if target_model in already_extracted and already_extracted[target_model]['models']:
                print('*****POPULATING RELATED:', target_model, field_name, '*****', end='\n')
                print(already_extracted[target_model]['models'])
                for ind, child_model in enumerate(already_extracted[target_model]['models']):
                    if issubclass(target_field, ManyToManyField):
                        raw_data = already_extracted[target_model]['raw'][ind]
                        if raw_data[field_name] == model_id:
                            setattr(model, related, child_model)

                    elif isinstance(getattr(child_model, field_name), ormar.Model):
                        if getattr(child_model, field_name).pk == model_id:
                            if reverse:
                                setattr(model, related, child_model)
                            else:
                                setattr(child_model, related, model)

                    else:  # we have not reverse relation and related_model is a pk value
                        setattr(model, related, child_model)

        return model

    async def prefetch_related(self, models: Sequence["Model"], rows: List):
        return await self._prefetch_related_models(models=models, rows=rows)

    async def _prefetch_related_models(self,
                                       models: Sequence["Model"],
                                       rows: List) -> Sequence["Model"]:
        already_extracted = {self.model.get_name(): {'raw': rows, 'models': models}}
        for related in self._prefetch_related:
            target_model = self.model
            fields = self._columns
            exclude_fields = self._exclude_columns
            for part in related.split('__'):
                fields = target_model.get_included(fields, part)
                select_related = []
                exclude_fields = target_model.get_excluded(exclude_fields, part)

                target_field = target_model.Meta.model_fields[part]
                reverse = False
                if target_field.virtual or issubclass(target_field, ManyToManyField):
                    reverse = True

                if issubclass(target_field, ManyToManyField):
                    select_related = [target_field.through.get_name()]

                parent_model = target_model
                target_model = target_field.to

                if target_model.get_name() not in already_extracted:
                    filter_clauses = self._get_filter_for_prefetch(already_extracted=already_extracted,
                                                                   parent_model=parent_model,
                                                                   target_model=target_model,
                                                                   reverse=reverse)
                    if not filter_clauses:  # related field is empty
                        continue

                    query_target = target_model
                    table_prefix = ''
                    if issubclass(target_field, ManyToManyField):
                        query_target = target_field.through
                        select_related = [target_field.to.get_name()]
                        table_prefix = target_field.to.Meta.alias_manager.resolve_relation_join(
                            from_table=query_target.Meta.tablename, to_table=target_field.to.Meta.tablename)

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
                    print(expr.compile(compile_kwargs={"literal_binds": True}))
                    rows = await self.database.fetch_all(expr)
                    already_extracted[target_model.get_name()] = {'raw': rows, 'models': []}
                    if part == related.split('__')[-1]:
                        for row in rows:
                            item = target_model.extract_prefixed_table_columns(
                                item={},
                                row=row,
                                table_prefix=table_prefix,
                                fields=fields,
                                exclude_fields=exclude_fields
                            )
                            instance = target_model(**item)
                            already_extracted[target_model.get_name()]['models'].append(instance)

            target_model = self.model
            fields = self._columns
            exclude_fields = self._exclude_columns
            for part in related.split('__')[:-1]:
                fields = target_model.get_included(fields, part)
                exclude_fields = target_model.get_excluded(exclude_fields, part)

                target_field = target_model.Meta.model_fields[part]
                target_model = target_field.to
                table_prefix = ''

                if issubclass(target_field, ManyToManyField):
                    from_table = target_field.through.Meta.tablename
                    to_name = target_field.to.Meta.tablename
                    table_prefix = target_field.to.Meta.alias_manager.resolve_relation_join(
                        from_table=from_table, to_table=to_name)

                for row in already_extracted.get(target_model.get_name(), {}).get('raw', []):
                    item = target_model.extract_prefixed_table_columns(
                        item={},
                        row=row,
                        table_prefix=table_prefix,
                        fields=fields,
                        exclude_fields=exclude_fields
                    )
                    instance = target_model(**item)
                    instance = self._populate_nested_related(model=instance,
                                                             already_extracted=already_extracted)

                    already_extracted[target_model.get_name()]['models'].append(instance)
        final_models = []
        for model in models:
            final_models.append(self._populate_nested_related(model=model,
                                                              already_extracted=already_extracted))
        return models
