from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    TYPE_CHECKING,
    Type,
    TypeVar,
    Union,
    cast,
)

import sqlalchemy

from ormar.models import NewBaseModel  # noqa: I202
from ormar.models.helpers.models import group_related_list


if TYPE_CHECKING:  # pragma: no cover
    from ormar.fields import ForeignKeyField
    from ormar.models import T
else:
    T = TypeVar("T", bound="ModelRow")


class ModelRow(NewBaseModel):
    @classmethod
    def from_row(  # noqa: CFQ002
        cls: Type["ModelRow"],
        row: sqlalchemy.engine.ResultProxy,
        source_model: Type[T],
        select_related: List = None,
        related_models: Any = None,
        related_field: Type["ForeignKeyField"] = None,
        fields: Optional[Union[Dict, Set]] = None,
        exclude_fields: Optional[Union[Dict, Set]] = None,
        current_relation_str: str = "",
    ) -> Optional[T]:
        """
        Model method to convert raw sql row from database into ormar.Model instance.
        Traverses nested models if they were specified in select_related for query.

        Called recurrently and returns model instance if it's present in the row.
        Note that it's processing one row at a time, so if there are duplicates of
        parent row that needs to be joined/combined
        (like parent row in sql join with 2+ child rows)
        instances populated in this method are later combined in the QuerySet.
        Other method working directly on raw database results is in prefetch_query,
        where rows are populated in a different way as they do not have
        nested models in result.

        :param current_relation_str: name of the relation field
        :type current_relation_str: str
        :param source_model: model on which relation was defined
        :type source_model: Type[Model]
        :param row: raw result row from the database
        :type row: sqlalchemy.engine.result.ResultProxy
        :param select_related: list of names of related models fetched from database
        :type select_related: List
        :param related_models: list or dict of related models
        :type related_models: Union[List, Dict]
        :param related_field: field with relation declaration
        :type related_field: Type[ForeignKeyField]
        :param fields: fields and related model fields to include
        if provided only those are included
        :type fields: Optional[Union[Dict, Set]]
        :param exclude_fields: fields and related model fields to exclude
        excludes the fields even if they are provided in fields
        :type exclude_fields: Optional[Union[Dict, Set]]
        :return: returns model if model is populated from database
        :rtype: Optional[Model]
        """
        item: Dict[str, Any] = {}
        select_related = select_related or []
        related_models = related_models or []
        table_prefix = ""

        if select_related:
            source_model = cast(Type[T], cls)
            related_models = group_related_list(select_related)

        if related_field:
            table_prefix = cls.Meta.alias_manager.resolve_relation_alias_after_complex(
                source_model=source_model,
                relation_str=current_relation_str,
                relation_field=related_field,
            )

        item = cls.populate_nested_models_from_row(
            item=item,
            row=row,
            related_models=related_models,
            fields=fields,
            exclude_fields=exclude_fields,
            current_relation_str=current_relation_str,
            source_model=source_model,
        )
        item = cls.extract_prefixed_table_columns(
            item=item,
            row=row,
            table_prefix=table_prefix,
            fields=fields,
            exclude_fields=exclude_fields,
        )

        instance: Optional[T] = None
        if item.get(cls.Meta.pkname, None) is not None:
            item["__excluded__"] = cls.get_names_to_exclude(
                fields=fields, exclude_fields=exclude_fields
            )
            instance = cast(T, cls(**item))
            instance.set_save_status(True)
        return instance

    @classmethod
    def populate_nested_models_from_row(  # noqa: CFQ002
        cls,
        item: dict,
        row: sqlalchemy.engine.ResultProxy,
        source_model: Type[T],
        related_models: Any,
        fields: Optional[Union[Dict, Set]] = None,
        exclude_fields: Optional[Union[Dict, Set]] = None,
        current_relation_str: str = None,
    ) -> dict:
        """
        Traverses structure of related models and populates the nested models
        from the database row.
        Related models can be a list if only directly related models are to be
        populated, converted to dict if related models also have their own related
        models to be populated.

        Recurrently calls from_row method on nested instances and create nested
        instances. In the end those instances are added to the final model dictionary.

        :param source_model: source model from which relation started
        :type source_model: Type[Model]
        :param current_relation_str: joined related parts into one string
        :type current_relation_str: str
        :param item: dictionary of already populated nested models, otherwise empty dict
        :type item: Dict
        :param row: raw result row from the database
        :type row: sqlalchemy.engine.result.ResultProxy
        :param related_models: list or dict of related models
        :type related_models: Union[Dict, List]
        :param fields: fields and related model fields to include -
        if provided only those are included
        :type fields: Optional[Union[Dict, Set]]
        :param exclude_fields: fields and related model fields to exclude
        excludes the fields even if they are provided in fields
        :type exclude_fields: Optional[Union[Dict, Set]]
        :return: dictionary with keys corresponding to model fields names
        and values are database values
        :rtype: Dict
        """

        for related in related_models:
            relation_str = (
                "__".join([current_relation_str, related])
                if current_relation_str
                else related
            )
            field = cls.Meta.model_fields[related]
            field = cast(Type["ForeignKeyField"], field)
            fields = cls.get_included(fields, related)
            exclude_fields = cls.get_excluded(exclude_fields, related)
            model_cls = field.to

            remainder = None
            if isinstance(related_models, dict) and related_models[related]:
                remainder = related_models[related]
            child = model_cls.from_row(
                row,
                related_models=remainder,
                related_field=field,
                fields=fields,
                exclude_fields=exclude_fields,
                current_relation_str=relation_str,
                source_model=source_model,
            )
            item[model_cls.get_column_name_from_alias(related)] = child
            if field.is_multi and child:
                # TODO: way to figure out which side should be populated?
                through_name = cls.Meta.model_fields[related].through.get_name()
                # for now it's nested dict, should be instance?
                through_child = cls.populate_through_instance(
                    row=row,
                    related=related,
                    through_name=through_name,
                    fields=fields,
                    exclude_fields=exclude_fields,
                )
                item[through_name] = through_child
                setattr(child, through_name, through_child)
                child.set_save_status(True)

        return item

    @classmethod
    def populate_through_instance(
        cls,
        row: sqlalchemy.engine.ResultProxy,
        through_name: str,
        related: str,
        fields: Optional[Union[Dict, Set]] = None,
        exclude_fields: Optional[Union[Dict, Set]] = None,
    ) -> Dict:
        # TODO: fix excludes and includes
        fields = cls.get_included(fields, through_name)
        # exclude_fields = cls.get_excluded(exclude_fields, through_name)
        model_cls = cls.Meta.model_fields[through_name].to
        exclude_fields = model_cls.extract_related_names()
        table_prefix = cls.Meta.alias_manager.resolve_relation_alias(
            from_model=cls, relation_name=related
        )
        child = model_cls.extract_prefixed_table_columns(
            item={},
            row=row,
            table_prefix=table_prefix,
            fields=fields,
            exclude_fields=exclude_fields,
        )
        return child

    @classmethod
    def extract_prefixed_table_columns(  # noqa CCR001
        cls,
        item: dict,
        row: sqlalchemy.engine.result.ResultProxy,
        table_prefix: str,
        fields: Optional[Union[Dict, Set]] = None,
        exclude_fields: Optional[Union[Dict, Set]] = None,
    ) -> dict:
        """
        Extracts own fields from raw sql result, using a given prefix.
        Prefix changes depending on the table's position in a join.

        If the table is a main table, there is no prefix.
        All joined tables have prefixes to allow duplicate column names,
        as well as duplicated joins to the same table from multiple different tables.

        Extracted fields populates the related dict later used to construct a Model.

        Used in Model.from_row and PrefetchQuery._populate_rows methods.

        :param item: dictionary of already populated nested models, otherwise empty dict
        :type item: Dict
        :param row: raw result row from the database
        :type row: sqlalchemy.engine.result.ResultProxy
        :param table_prefix: prefix of the table from AliasManager
        each pair of tables have own prefix (two of them depending on direction) -
        used in joins to allow multiple joins to the same table.
        :type table_prefix: str
        :param fields: fields and related model fields to include -
        if provided only those are included
        :type fields: Optional[Union[Dict, Set]]
        :param exclude_fields: fields and related model fields to exclude
        excludes the fields even if they are provided in fields
        :type exclude_fields: Optional[Union[Dict, Set]]
        :return: dictionary with keys corresponding to model fields names
        and values are database values
        :rtype: Dict
        """
        # databases does not keep aliases in Record for postgres, change to raw row
        source = row._row if cls.db_backend_name() == "postgresql" else row

        selected_columns = cls.own_table_columns(
            model=cls,
            fields=fields or {},
            exclude_fields=exclude_fields or {},
            use_alias=False,
        )

        for column in cls.Meta.table.columns:
            alias = cls.get_column_name_from_alias(column.name)
            if alias not in item and alias in selected_columns:
                prefixed_name = (
                    f'{table_prefix + "_" if table_prefix else ""}{column.name}'
                )
                item[alias] = source[prefixed_name]

        return item
