from typing import Callable, Dict, List, TYPE_CHECKING, Tuple, Type, Union, cast

from ormar.models.mixins.relation_mixin import RelationMixin

if TYPE_CHECKING:  # pragma: no cover
    from ormar.fields import ForeignKeyField, ManyToManyField


class PrefetchQueryMixin(RelationMixin):
    """
    Used in PrefetchQuery to extract ids and names of models to prefetch.
    """

    if TYPE_CHECKING:  # pragma no cover
        from ormar import Model

        get_name: Callable  # defined in NewBaseModel

    @staticmethod
    def get_clause_target_and_filter_column_name(
        parent_model: Type["Model"],
        target_model: Type["Model"],
        reverse: bool,
        related: str,
    ) -> Tuple[Type["Model"], Union[str, Dict]]:
        """
        Returns Model on which query clause should be performed and name of the column.

        :param parent_model: related model that the relation lead to
        :type parent_model: Type[Model]
        :param target_model: model on which query should be perfomed
        :type target_model: Type[Model]
        :param reverse: flag if the relation is reverse
        :type reverse: bool
        :param related: name of the relation field
        :type related: str
        :return: Model on which query clause should be performed and name of the column
        :rtype: Tuple[Type[Model], str]
        """
        if reverse:
            field_name = parent_model.Meta.model_fields[related].get_related_name()
            field = target_model.Meta.model_fields[field_name]
            if field.is_multi:
                field = cast("ManyToManyField", field)
                field_name = field.default_target_field_name()
                sub_field = field.through.Meta.model_fields[field_name]
                if sub_field.is_compound:
                    return (
                        field.through,
                        cast(Dict[str, str], sub_field.get_reversed_names()),
                    )
                return field.through, sub_field.get_alias()
            if field.is_compound:
                return target_model, cast(Dict[str, str], field.get_reversed_names())
            return target_model, field.get_alias()
        if target_model.has_pk_constraint:
            field = parent_model.Meta.model_fields[related]
            return target_model, field.names
        target_field = target_model.get_column_alias(target_model.Meta.pkname)
        return target_model, target_field

    @staticmethod
    def get_column_name_for_id_extraction(
        parent_model: Type["Model"], reverse: bool, related: str, use_raw: bool,
    ) -> Union[str, List]:
        """
        Returns name of the column that should be used to extract ids from model.
        Depending on the relation side it's either primary key column of parent model
        or field name specified by related parameter.

        :param parent_model: model from which id column should be extracted
        :type parent_model: Type[Model]
        :param reverse: flag if the relation is reverse
        :type reverse: bool
        :param related: name of the relation field
        :type related: str
        :param use_raw: flag if aliases or field names should be used
        :type use_raw: bool
        :return:
        :rtype:
        """
        if reverse:
            result = (
                parent_model.pk_aliases_list if use_raw else parent_model.pk_names_list
            )
            return result[0] if len(result) == 1 else result
        column = parent_model.Meta.model_fields[related]
        if column.is_compound:
            aliases = list(column.names.values())
            return (
                aliases
                if use_raw
                else [parent_model.get_column_name_from_alias(col) for col in aliases]
            )
        return column.get_alias() if use_raw else column.name

    @classmethod
    def get_related_field_name(
        cls, target_field: "ForeignKeyField"
    ) -> Union[str, List[str]]:
        """
        Returns name of the relation field that should be used in prefetch query.
        This field is later used to register relation in prefetch query,
        populate relations dict, and populate nested model in prefetch query.

        :param target_field: relation field that should be used in prefetch
        :type target_field: Type[BaseField]
        :return: name of the field
        :rtype: str
        """
        if target_field.is_multi:
            return cls.get_name()
        if target_field.virtual:
            return target_field.get_related_name()
        return (
            target_field.to.Meta.pkname
            if not target_field.is_compound
            else target_field.to.pk_aliases_list
        )

    @classmethod
    def get_filtered_names_to_extract(cls, prefetch_dict: Dict) -> List:
        """
        Returns list of related fields names that should be followed to prefetch related
        models from.

        List of models is translated into dict to assure each model is extracted only
        once in one query, that's why this function accepts prefetch_dict not list.

        Only relations from current model are returned.

        :param prefetch_dict: dictionary of fields to extract
        :type prefetch_dict: Dict
        :return: list of fields names to extract
        :rtype: List
        """
        related_to_extract = []
        if prefetch_dict and prefetch_dict is not Ellipsis:
            related_to_extract = [
                related
                for related in cls.extract_related_names()
                if related in prefetch_dict
            ]
        return related_to_extract
