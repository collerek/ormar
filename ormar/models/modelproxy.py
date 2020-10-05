import inspect
from typing import Dict, List, Set, TYPE_CHECKING, Type, TypeVar, Union

import ormar
from ormar.exceptions import RelationshipInstanceError
from ormar.fields import BaseField
from ormar.fields.foreign_key import ForeignKeyField
from ormar.models.metaclass import ModelMeta

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model
    from ormar.models import NewBaseModel

Field = TypeVar("Field", bound=BaseField)


class ModelTableProxy:
    if TYPE_CHECKING:  # pragma no cover
        Meta: ModelMeta

    def dict(self):  # noqa A003
        raise NotImplementedError  # pragma no cover

    def _extract_own_model_fields(self) -> Dict:
        related_names = self.extract_related_names()
        self_fields = {k: v for k, v in self.dict().items() if k not in related_names}
        return self_fields

    @classmethod
    def extract_db_own_fields(cls) -> Set:
        related_names = cls.extract_related_names()
        self_fields = {
            name for name in cls.Meta.model_fields.keys() if name not in related_names
        }
        return self_fields

    @classmethod
    def substitute_models_with_pks(cls, model_dict: Dict) -> Dict:
        for field in cls.extract_related_names():
            field_value = model_dict.get(field, None)
            if field_value is not None:
                target_field = cls.Meta.model_fields[field]
                target_pkname = target_field.to.Meta.pkname
                if isinstance(field_value, ormar.Model):
                    model_dict[field] = getattr(field_value, target_pkname)
                else:
                    model_dict[field] = field_value.get(target_pkname)
        return model_dict

    @classmethod
    def extract_related_names(cls) -> Set:
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
            return cls.extract_related_names()
        related_names = set()
        for name, field in cls.Meta.model_fields.items():
            if (
                inspect.isclass(field)
                and issubclass(field, ForeignKeyField)
                and field.nullable
            ):
                related_names.add(name)
        return related_names

    def _extract_model_db_fields(self) -> Dict:
        self_fields = self._extract_own_model_fields()
        self_fields = {
            k: v for k, v in self_fields.items() if k in self.Meta.table.columns
        }
        for field in self._extract_db_related_names():
            target_pk_name = self.Meta.model_fields[field].to.Meta.pkname
            target_field = getattr(self, field)
            self_fields[field] = getattr(target_field, target_pk_name, None)
        return self_fields

    @staticmethod
    def resolve_relation_name(
        item: Union["NewBaseModel", Type["NewBaseModel"]],
        related: Union["NewBaseModel", Type["NewBaseModel"]],
    ) -> str:
        for name, field in item.Meta.model_fields.items():
            if issubclass(field, ForeignKeyField):
                # fastapi is creating clones of response model
                # that's why it can be a subclass of the original model
                # so we need to compare Meta too as this one is copied as is
                if field.to == related.__class__ or field.to.Meta == related.Meta:
                    return name
        raise ValueError(
            f"No relation between {item.get_name()} and {related.get_name()}"
        )  # pragma nocover

    @staticmethod
    def resolve_relation_field(
        item: Union["Model", Type["Model"]], related: Union["Model", Type["Model"]]
    ) -> Union[Type[BaseField], Type[ForeignKeyField]]:
        name = ModelTableProxy.resolve_relation_name(item, related)
        to_field = item.Meta.model_fields.get(name)
        if not to_field:  # pragma no cover
            raise RelationshipInstanceError(
                f"Model {item.__class__} does not have "
                f"reference to model {related.__class__}"
            )
        return to_field

    @classmethod
    def merge_instances_list(cls, result_rows: List["Model"]) -> List["Model"]:
        merged_rows: List["Model"] = []
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

    @staticmethod
    def own_table_columns(
        model: Type["Model"], fields: List, nested: bool = False
    ) -> List[str]:
        column_names = [col.name for col in model.Meta.table.columns]
        if not fields:
            return column_names

        if not nested:
            columns = [
                name for name in fields if "__" not in name and name in column_names
            ]
        else:
            model_name = f"{model.get_name()}__"
            columns = [
                name[(name.find(model_name) + len(model_name)) :]  # noqa: E203
                for name in fields
                if f"{model.get_name()}__" in name
            ]

        # if the model is in select and no columns in fields, all implied
        if not columns:
            columns = column_names

        # always has to return pk column
        if model.Meta.pkname not in columns:
            columns.append(model.Meta.pkname)
        return columns
