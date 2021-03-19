from typing import (
    Any,
    Dict,
    List,
    Optional,
    TYPE_CHECKING,
    Tuple,
    Type,
    Union,
    cast,
)

import sqlalchemy

from ormar.models import NewBaseModel  # noqa: I202
from ormar.models.excludable import ExcludableItems
from ormar.models.helpers.models import group_related_list

if TYPE_CHECKING:  # pragma: no cover
    from ormar.fields import ForeignKeyField
    from ormar.models import Model


class ModelRow(NewBaseModel):
    @classmethod
    def from_row(  # noqa: CFQ002
        cls,
        row: sqlalchemy.engine.ResultProxy,
        source_model: Type["Model"],
        select_related: List = None,
        related_models: Any = None,
        related_field: "ForeignKeyField" = None,
        excludable: ExcludableItems = None,
        current_relation_str: str = "",
        proxy_source_model: Optional[Type["Model"]] = None,
        used_prefixes: List[str] = None,
    ) -> Optional["Model"]:
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

        :param used_prefixes: list of already extracted prefixes
        :type used_prefixes: List[str]
        :param proxy_source_model: source model from which querysetproxy is constructed
        :type proxy_source_model: Optional[Type["ModelRow"]]
        :param excludable: structure of fields to include and exclude
        :type excludable: ExcludableItems
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
        :type related_field: ForeignKeyField
        :return: returns model if model is populated from database
        :rtype: Optional[Model]
        """
        item: Dict[str, Any] = {}
        select_related = select_related or []
        related_models = related_models or []
        table_prefix = ""
        used_prefixes = used_prefixes if used_prefixes is not None else []
        excludable = excludable or ExcludableItems()

        if select_related:
            related_models = group_related_list(select_related)

        if related_field:
            table_prefix = cls._process_table_prefix(
                source_model=source_model,
                current_relation_str=current_relation_str,
                related_field=related_field,
                used_prefixes=used_prefixes,
            )

        item = cls._populate_nested_models_from_row(
            item=item,
            row=row,
            related_models=related_models,
            excludable=excludable,
            current_relation_str=current_relation_str,
            source_model=source_model,  # type: ignore
            proxy_source_model=proxy_source_model,  # type: ignore
            table_prefix=table_prefix,
            used_prefixes=used_prefixes,
        )
        item = cls.extract_prefixed_table_columns(
            item=item, row=row, table_prefix=table_prefix, excludable=excludable
        )

        instance: Optional["Model"] = None
        if item.get(cls.Meta.pkname, None) is not None:
            item["__excluded__"] = cls.get_names_to_exclude(
                excludable=excludable, alias=table_prefix
            )
            instance = cast("Model", cls(**item))
            instance.set_save_status(True)
        return instance

    @classmethod
    def _process_table_prefix(
        cls,
        source_model: Type["Model"],
        current_relation_str: str,
        related_field: "ForeignKeyField",
        used_prefixes: List[str],
    ) -> str:
        """

        :param source_model: model on which relation was defined
        :type source_model: Type[Model]
        :param current_relation_str: current relation string
        :type current_relation_str: str
        :param related_field: field with relation declaration
        :type related_field: "ForeignKeyField"
        :param used_prefixes: list of already extracted prefixes
        :type used_prefixes: List[str]
        :return: table_prefix to use
        :rtype: str
        """
        if related_field.is_multi:
            previous_model = related_field.through
        else:
            previous_model = related_field.owner
        table_prefix = cls.Meta.alias_manager.resolve_relation_alias(
            from_model=previous_model, relation_name=related_field.name
        )
        if not table_prefix or table_prefix in used_prefixes:
            manager = cls.Meta.alias_manager
            table_prefix = manager.resolve_relation_alias_after_complex(
                source_model=source_model,
                relation_str=current_relation_str,
                relation_field=related_field,
            )
        used_prefixes.append(table_prefix)
        return table_prefix

    @classmethod
    def _populate_nested_models_from_row(  # noqa: CFQ002
        cls,
        item: dict,
        row: sqlalchemy.engine.ResultProxy,
        source_model: Type["Model"],
        related_models: Any,
        excludable: ExcludableItems,
        table_prefix: str,
        used_prefixes: List[str],
        current_relation_str: str = None,
        proxy_source_model: Type["Model"] = None,
    ) -> dict:
        """
        Traverses structure of related models and populates the nested models
        from the database row.
        Related models can be a list if only directly related models are to be
        populated, converted to dict if related models also have their own related
        models to be populated.

        Recurrently calls from_row method on nested instances and create nested
        instances. In the end those instances are added to the final model dictionary.

        :param proxy_source_model: source model from which querysetproxy is constructed
        :type proxy_source_model: Optional[Type["ModelRow"]]
        :param excludable: structure of fields to include and exclude
        :type excludable: ExcludableItems
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
        :return: dictionary with keys corresponding to model fields names
        and values are database values
        :rtype: Dict
        """

        for related in related_models:
            field = cls.Meta.model_fields[related]
            field = cast("ForeignKeyField", field)
            model_cls = field.to
            model_excludable = excludable.get(
                model_cls=cast(Type["Model"], cls), alias=table_prefix
            )
            if model_excludable.is_excluded(related):
                return item

            relation_str, remainder = cls._process_remainder_and_relation_string(
                related_models=related_models,
                current_relation_str=current_relation_str,
                related=related,
            )
            child = model_cls.from_row(
                row,
                related_models=remainder,
                related_field=field,
                excludable=excludable,
                current_relation_str=relation_str,
                source_model=source_model,
                proxy_source_model=proxy_source_model,
                used_prefixes=used_prefixes,
            )
            item[model_cls.get_column_name_from_alias(related)] = child
            if field.is_multi and child:
                cls._populate_through_instance(
                    row=row,
                    item=item,
                    related=related,
                    excludable=excludable,
                    child=child,
                    proxy_source_model=proxy_source_model,
                )

        return item

    @staticmethod
    def _process_remainder_and_relation_string(
        related_models: Union[Dict, List],
        current_relation_str: Optional[str],
        related: str,
    ) -> Tuple[str, Optional[Union[Dict, List]]]:
        """
        Process remainder models and relation string

        :param related_models: list or dict of related models
        :type related_models: Union[Dict, List]
        :param current_relation_str: current relation string
        :type current_relation_str: Optional[str]
        :param related: name of the relation
        :type related: str
        """
        relation_str = (
            "__".join([current_relation_str, related])
            if current_relation_str
            else related
        )

        remainder = None
        if isinstance(related_models, dict) and related_models[related]:
            remainder = related_models[related]
        return relation_str, remainder

    @classmethod
    def _populate_through_instance(  # noqa: CFQ002
        cls,
        row: sqlalchemy.engine.ResultProxy,
        item: Dict,
        related: str,
        excludable: ExcludableItems,
        child: "Model",
        proxy_source_model: Optional[Type["Model"]],
    ) -> None:
        """
        Populates the through model on reverse side of current query.
        Normally it's child class, unless the query is from queryset.

        :param row: row from db result
        :type row: sqlalchemy.engine.ResultProxy
        :param item: parent item dict
        :type item: Dict
        :param related: current relation name
        :type related: str
        :param excludable: structure of fields to include and exclude
        :type excludable: ExcludableItems
        :param child: child item of parent
        :type child: "Model"
        :param proxy_source_model: source model from which querysetproxy is constructed
        :type proxy_source_model: Type["Model"]
        """
        through_name = cls.Meta.model_fields[related].through.get_name()
        through_child = cls._create_through_instance(
            row=row, related=related, through_name=through_name, excludable=excludable,
        )

        if child.__class__ != proxy_source_model:
            setattr(child, through_name, through_child)
        else:
            item[through_name] = through_child
        child.set_save_status(True)

    @classmethod
    def _create_through_instance(
        cls,
        row: sqlalchemy.engine.ResultProxy,
        through_name: str,
        related: str,
        excludable: ExcludableItems,
    ) -> "ModelRow":
        """
        Initialize the through model from db row.
        Excluded all relation fields and other exclude/include set in excludable.

        :param row: loaded row from database
        :type row: sqlalchemy.engine.ResultProxy
        :param through_name: name of the through field
        :type through_name: str
        :param related: name of the relation
        :type related: str
        :param excludable: structure of fields to include and exclude
        :type excludable: ExcludableItems
        :return: initialized through model without relation
        :rtype: "ModelRow"
        """
        model_cls = cls.Meta.model_fields[through_name].to
        table_prefix = cls.Meta.alias_manager.resolve_relation_alias(
            from_model=cls, relation_name=related
        )
        # remove relations on through field
        model_excludable = excludable.get(model_cls=model_cls, alias=table_prefix)
        model_excludable.set_values(
            value=model_cls.extract_related_names(), is_exclude=True
        )
        child_dict = model_cls.extract_prefixed_table_columns(
            item={}, row=row, excludable=excludable, table_prefix=table_prefix
        )
        child_dict["__excluded__"] = model_cls.get_names_to_exclude(
            excludable=excludable, alias=table_prefix
        )
        child = model_cls(**child_dict)  # type: ignore
        return child

    @classmethod
    def extract_prefixed_table_columns(
        cls,
        item: dict,
        row: sqlalchemy.engine.result.ResultProxy,
        table_prefix: str,
        excludable: ExcludableItems,
    ) -> Dict:
        """
        Extracts own fields from raw sql result, using a given prefix.
        Prefix changes depending on the table's position in a join.

        If the table is a main table, there is no prefix.
        All joined tables have prefixes to allow duplicate column names,
        as well as duplicated joins to the same table from multiple different tables.

        Extracted fields populates the related dict later used to construct a Model.

        Used in Model.from_row and PrefetchQuery._populate_rows methods.

        :param excludable: structure of fields to include and exclude
        :type excludable: ExcludableItems
        :param item: dictionary of already populated nested models, otherwise empty dict
        :type item: Dict
        :param row: raw result row from the database
        :type row: sqlalchemy.engine.result.ResultProxy
        :param table_prefix: prefix of the table from AliasManager
        each pair of tables have own prefix (two of them depending on direction) -
        used in joins to allow multiple joins to the same table.
        :type table_prefix: str
        :return: dictionary with keys corresponding to model fields names
        and values are database values
        :rtype: Dict
        """
        selected_columns = cls.own_table_columns(
            model=cls, excludable=excludable, alias=table_prefix, use_alias=False,
        )

        column_prefix = table_prefix + "_" if table_prefix else ""
        for column in cls.Meta.table.columns:
            alias = cls.get_column_name_from_alias(column.name)
            if alias not in item and alias in selected_columns:
                prefixed_name = f"{column_prefix}{column.name}"
                item[alias] = row[prefixed_name]

        return item
