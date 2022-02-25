from collections import OrderedDict
from typing import Dict, List, Optional, TYPE_CHECKING, cast

import ormar
from ormar.queryset.utils import translate_list_to_dict

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


class MergeModelMixin:
    """
    Used to merge models instances returned by database,
    but already initialized to ormar Models.keys

    Models can duplicate during joins when parent model has multiple child rows,
    in the end all parent (main) models should be unique.
    """

    @classmethod
    def merge_instances_list(cls, result_rows: List["Model"]) -> List["Model"]:
        """
        Merges a list of models into list of unique models.

        Models can duplicate during joins when parent model has multiple child rows,
        in the end all parent (main) models should be unique.

        :param result_rows: list of already initialized Models with child models
        populated, each instance is one row in db and some models can duplicate
        :type result_rows: List["Model"]
        :return: list of merged models where each main model is unique
        :rtype: List["Model"]
        """
        merged_rows: List["Model"] = []
        grouped_instances: OrderedDict = OrderedDict()

        for model in result_rows:
            grouped_instances.setdefault(model.pk, []).append(model)

        for group in grouped_instances.values():
            model = group.pop(0)
            if group:
                for next_model in group:
                    model = cls.merge_two_instances(next_model, model)
            merged_rows.append(model)

        return merged_rows

    @classmethod
    def merge_two_instances(
        cls, one: "Model", other: "Model", relation_map: Dict = None
    ) -> "Model":
        """
        Merges current (other) Model and previous one (one) and returns the current
        Model instance with data merged from previous one.

        If needed it's calling itself recurrently and merges also children models.

        :param relation_map: map of models relations to follow
        :type relation_map: Dict
        :param one: previous model instance
        :type one: Model
        :param other: current model instance
        :type other: Model
        :return: current Model instance with data merged from previous one.
        :rtype: Model
        """
        relation_map = (
            relation_map
            if relation_map is not None
            else translate_list_to_dict(one._iterate_related_models())
        )
        for field_name in relation_map:
            current_field = getattr(one, field_name)
            other_value = getattr(other, field_name, [])
            if isinstance(current_field, list):
                value_to_set = cls._merge_items_lists(
                    field_name=field_name,
                    current_field=current_field,
                    other_value=other_value,
                    relation_map=relation_map,
                )
                setattr(other, field_name, value_to_set)
            elif (
                isinstance(current_field, ormar.Model)
                and isinstance(other_value, ormar.Model)
                and current_field.pk == other_value.pk
            ):
                setattr(
                    other,
                    field_name,
                    cls.merge_two_instances(
                        current_field,
                        other_value,
                        relation_map=one._skip_ellipsis(  # type: ignore
                            relation_map, field_name, default_return=dict()
                        ),
                    ),
                )
        other.set_save_status(True)
        return other

    @classmethod
    def _merge_items_lists(
        cls,
        field_name: str,
        current_field: List,
        other_value: List,
        relation_map: Optional[Dict],
    ) -> List:
        """
        Takes two list of nested models and process them going deeper
        according with the map.

        If model from one's list is in other -> they are merged with relations
        to follow passed from map.

        If one's model is not in other it's simply appended to the list.

        :param field_name: name of the current relation field
        :type field_name: str
        :param current_field: list of nested models from one model
        :type current_field: List[Model]
        :param other_value: list of nested models from other model
        :type other_value: List[Model]
        :param relation_map: map of relations to follow
        :type relation_map: Dict
        :return: merged list of models
        :rtype: List[Model]
        """
        value_to_set = [x for x in other_value]
        for cur_field in current_field:
            if cur_field in other_value:
                old_value = next((x for x in other_value if x == cur_field), None)
                new_val = cls.merge_two_instances(
                    cur_field,
                    cast("Model", old_value),
                    relation_map=cur_field._skip_ellipsis(  # type: ignore
                        relation_map, field_name, default_return=dict()
                    ),
                )
                value_to_set = [x for x in value_to_set if x != cur_field] + [new_val]
            else:
                value_to_set.append(cur_field)
        return value_to_set
