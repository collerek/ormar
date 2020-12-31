from typing import Callable, Dict, List, TYPE_CHECKING, Tuple, Type

import ormar
from ormar.fields import BaseField
from ormar.models.mixins.relation_mixin import RelationMixin


class PrefetchQueryMixin(RelationMixin):
    if TYPE_CHECKING:  # pragma no cover
        from ormar import Model

        get_name: Callable  # defined in NewBaseModel

    @staticmethod
    def get_clause_target_and_filter_column_name(
        parent_model: Type["Model"],
        target_model: Type["Model"],
        reverse: bool,
        related: str,
    ) -> Tuple[Type["Model"], str]:
        if reverse:
            field_name = (
                parent_model.Meta.model_fields[related].related_name
                or parent_model.get_name() + "s"
            )
            field = target_model.Meta.model_fields[field_name]
            if issubclass(field, ormar.fields.ManyToManyField):
                field_name = field.default_target_field_name()
                sub_field = field.through.Meta.model_fields[field_name]
                return field.through, sub_field.get_alias()
            return target_model, field.get_alias()
        target_field = target_model.get_column_alias(target_model.Meta.pkname)
        return target_model, target_field

    @staticmethod
    def get_column_name_for_id_extraction(
        parent_model: Type["Model"], reverse: bool, related: str, use_raw: bool,
    ) -> str:
        if reverse:
            column_name = parent_model.Meta.pkname
            return (
                parent_model.get_column_alias(column_name) if use_raw else column_name
            )
        column = parent_model.Meta.model_fields[related]
        return column.get_alias() if use_raw else column.name

    @classmethod
    def get_related_field_name(cls, target_field: Type["BaseField"]) -> str:
        if issubclass(target_field, ormar.fields.ManyToManyField):
            return cls.get_name()
        if target_field.virtual:
            return target_field.related_name or cls.get_name() + "s"
        return target_field.to.Meta.pkname

    @classmethod
    def get_filtered_names_to_extract(cls, prefetch_dict: Dict) -> List:
        related_to_extract = []
        if prefetch_dict and prefetch_dict is not Ellipsis:
            related_to_extract = [
                related
                for related in cls.extract_related_names()
                if related in prefetch_dict
            ]
        return related_to_extract
