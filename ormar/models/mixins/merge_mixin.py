from collections import OrderedDict
from typing import List, TYPE_CHECKING

import ormar

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
    def merge_two_instances(cls, one: "Model", other: "Model") -> "Model":
        """
        Merges current (other) Model and previous one (one) and returns the current
        Model instance with data merged from previous one.

        If needed it's calling itself recurrently and merges also children models.

        :param one: previous model instance
        :type one: Model
        :param other: current model instance
        :type other: Model
        :return: current Model instance with data merged from previous one.
        :rtype: Model
        """
        for field in one.Meta.model_fields.keys():
            current_field = getattr(one, field)
            if isinstance(current_field, list) and not isinstance(
                current_field, ormar.Model
            ):
                setattr(other, field, current_field + getattr(other, field))
            elif (
                isinstance(current_field, ormar.Model)
                and current_field.pk == getattr(other, field).pk
            ):
                setattr(
                    other,
                    field,
                    cls.merge_two_instances(current_field, getattr(other, field)),
                )
        other.set_save_status(True)
        return other
