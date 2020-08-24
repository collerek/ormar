import copy
import inspect
from typing import List, Set, TYPE_CHECKING

import ormar
from ormar.fields.foreign_key import ForeignKeyField
from ormar.models.metaclass import ModelMeta

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


class ModelTableProxy:
    if TYPE_CHECKING:  # pragma no cover
        Meta: ModelMeta

    def dict():  # noqa A003
        raise NotImplementedError  # pragma no cover

    def _extract_own_model_fields(self) -> dict:
        related_names = self._extract_related_names()
        self_fields = {k: v for k, v in self.dict().items() if k not in related_names}
        return self_fields

    @classmethod
    def substitute_models_with_pks(cls, model_dict: dict) -> dict:
        model_dict = copy.deepcopy(model_dict)
        for field in cls._extract_related_names():
            if field in model_dict and model_dict.get(field) is not None:
                target_field = cls.Meta.model_fields[field]
                target_pkname = target_field.to.Meta.pkname
                if isinstance(model_dict.get(field), ormar.Model):
                    model_dict[field] = getattr(model_dict.get(field), target_pkname)
                else:
                    model_dict[field] = model_dict.get(field).get(target_pkname)
        return model_dict

    @classmethod
    def _extract_related_names(cls) -> Set:
        related_names = set()
        for name, field in cls.Meta.model_fields.items():
            if inspect.isclass(field) and issubclass(field, ForeignKeyField):
                related_names.add(name)
        return related_names

    @classmethod
    def _extract_db_related_names(cls) -> Set:
        related_names = set()
        for name, field in cls.Meta.model_fields.items():
            if (
                inspect.isclass(field)
                and issubclass(field, ForeignKeyField)
                and not field.virtual
            ):
                related_names.add(name)
        return related_names

    @classmethod
    def _exclude_related_names_not_required(cls, nested: bool = False) -> Set:
        if nested:
            return cls._extract_related_names()
        related_names = set()
        for name, field in cls.Meta.model_fields.items():
            if (
                inspect.isclass(field)
                and issubclass(field, ForeignKeyField)
                and field.nullable
            ):
                related_names.add(name)
        return related_names

    def _extract_model_db_fields(self) -> dict:
        self_fields = self._extract_own_model_fields()
        self_fields = {
            k: v for k, v in self_fields.items() if k in self.Meta.table.columns
        }
        for field in self._extract_db_related_names():
            target_pk_name = self.Meta.model_fields[field].to.Meta.pkname
            if getattr(self, field) is not None:
                self_fields[field] = getattr(getattr(self, field), target_pk_name)
        return self_fields

    @classmethod
    def merge_instances_list(cls, result_rows: List["Model"]) -> List["Model"]:
        merged_rows = []
        for index, model in enumerate(result_rows):
            if index > 0 and model.pk == merged_rows[-1].pk:
                merged_rows[-1] = cls.merge_two_instances(model, merged_rows[-1])
            else:
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
        return other
