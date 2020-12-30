from collections import OrderedDict
from typing import List, Sequence, TYPE_CHECKING

import ormar

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


class MergeModelMixin:
    @classmethod
    def merge_instances_list(cls, result_rows: Sequence["Model"]) -> Sequence["Model"]:
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
