import inspect
from collections import OrderedDict
from typing import Dict, List, Sequence, Set, TYPE_CHECKING, Type, TypeVar, Union

import ormar
from ormar.exceptions import RelationshipInstanceError
from ormar.fields import BaseField, ManyToManyField
from ormar.fields.foreign_key import ForeignKeyField
from ormar.models.metaclass import ModelMeta, expand_reverse_relationships

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model
    from ormar.models import NewBaseModel

    T = TypeVar("T", bound=Model)

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
    def substitute_models_with_pks(cls, model_dict: Dict) -> Dict:  # noqa  CCR001
        for field in cls.extract_related_names():
            field_value = model_dict.get(field, None)
            if field_value is not None:
                target_field = cls.Meta.model_fields[field]
                target_pkname = target_field.to.Meta.pkname
                if isinstance(field_value, ormar.Model):
                    model_dict[field] = getattr(field_value, target_pkname)
                elif field_value:
                    model_dict[field] = field_value.get(target_pkname)
                else:
                    model_dict.pop(field, None)
        return model_dict

    @classmethod
    def populate_default_values(cls, new_kwargs: Dict) -> Dict:
        for field_name, field in cls.Meta.model_fields.items():
            if field_name not in new_kwargs and field.has_default(use_server=False):
                new_kwargs[field_name] = field.get_default()
            # clear fields with server_default set as None
            if field.server_default is not None and not new_kwargs.get(field_name):
                new_kwargs.pop(field_name, None)
        return new_kwargs

    @classmethod
    def get_column_alias(cls, field_name: str) -> str:
        field = cls.Meta.model_fields.get(field_name)
        if field and field.alias is not None:
            return field.alias
        return field_name

    @classmethod
    def get_column_name_from_alias(cls, alias: str) -> str:
        for field_name, field in cls.Meta.model_fields.items():
            if field and field.alias == alias:
                return field_name
        return alias  # if not found it's not an alias but actual name

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
                and not issubclass(field, ManyToManyField)
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
            k: v
            for k, v in self_fields.items()
            if self.get_column_alias(k) in self.Meta.table.columns
        }
        for field in self._extract_db_related_names():
            target_pk_name = self.Meta.model_fields[field].to.Meta.pkname
            target_field = getattr(self, field)
            self_fields[field] = getattr(target_field, target_pk_name, None)
        return self_fields

    @staticmethod
    def resolve_relation_name(  # noqa CCR001
        item: Union["NewBaseModel", Type["NewBaseModel"]],
        related: Union["NewBaseModel", Type["NewBaseModel"]],
        register_missing: bool = True,
    ) -> str:
        for name, field in item.Meta.model_fields.items():
            if issubclass(field, ForeignKeyField):
                # fastapi is creating clones of response model
                # that's why it can be a subclass of the original model
                # so we need to compare Meta too as this one is copied as is
                if field.to == related.__class__ or field.to.Meta == related.Meta:
                    return name
        # fallback for not registered relation
        if register_missing:  # pragma nocover
            expand_reverse_relationships(related.__class__)  # type: ignore
            return ModelTableProxy.resolve_relation_name(
                item, related, register_missing=False
            )

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
    def translate_columns_to_aliases(cls, new_kwargs: Dict) -> Dict:
        for field_name, field in cls.Meta.model_fields.items():
            if field_name in new_kwargs:
                new_kwargs[field.get_alias()] = new_kwargs.pop(field_name)
        return new_kwargs

    @classmethod
    def translate_aliases_to_columns(cls, new_kwargs: Dict) -> Dict:
        for field_name, field in cls.Meta.model_fields.items():
            if field.alias and field.alias in new_kwargs:
                new_kwargs[field_name] = new_kwargs.pop(field.alias)
        return new_kwargs

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
        return other

    @staticmethod
    def _get_not_nested_columns_from_fields(
        model: Type["Model"],
        fields: List,
        exclude_fields: List,
        column_names: List[str],
        use_alias: bool = False,
    ) -> List[str]:
        fields = [model.get_column_alias(k) if not use_alias else k for k in fields]
        fields = fields or column_names
        exclude_fields = [
            model.get_column_alias(k) if not use_alias else k for k in exclude_fields
        ]
        columns = [
            name
            for name in fields
            if "__" not in name and name in column_names and name not in exclude_fields
        ]
        return columns

    @staticmethod
    def _get_nested_columns_from_fields(
        model: Type["Model"],
        fields: List,
        exclude_fields: List,
        column_names: List[str],
        use_alias: bool = False,
    ) -> List[str]:
        model_name = f"{model.get_name()}__"
        columns = [
            name[(name.find(model_name) + len(model_name)) :]  # noqa: E203
            for name in fields
            if f"{model.get_name()}__" in name
        ]
        columns = columns or column_names
        exclude_columns = [
            name[(name.find(model_name) + len(model_name)) :]  # noqa: E203
            for name in exclude_fields
            if f"{model.get_name()}__" in name
        ]
        columns = [model.get_column_alias(k) if not use_alias else k for k in columns]
        exclude_columns = [
            model.get_column_alias(k) if not use_alias else k for k in exclude_columns
        ]
        return [column for column in columns if column not in exclude_columns]

    @staticmethod
    def _populate_pk_column(
        model: Type["Model"], columns: List[str], use_alias: bool = False,
    ) -> List[str]:
        pk_alias = (
            model.get_column_alias(model.Meta.pkname)
            if not use_alias
            else model.Meta.pkname
        )
        if pk_alias not in columns:
            columns.append(pk_alias)
        return columns

    @staticmethod
    def own_table_columns(
        model: Type["Model"],
        fields: List,
        exclude_fields: List,
        nested: bool = False,
        use_alias: bool = False,
    ) -> List[str]:
        column_names = [
            model.get_column_name_from_alias(col.name) if use_alias else col.name
            for col in model.Meta.table.columns
        ]
        if not fields and not exclude_fields:
            return column_names

        if not nested:
            columns = ModelTableProxy._get_not_nested_columns_from_fields(
                model=model,
                fields=fields,
                exclude_fields=exclude_fields,
                column_names=column_names,
                use_alias=use_alias,
            )
        else:
            columns = ModelTableProxy._get_nested_columns_from_fields(
                model=model,
                fields=fields,
                exclude_fields=exclude_fields,
                column_names=column_names,
                use_alias=use_alias,
            )

        # always has to return pk column
        columns = ModelTableProxy._populate_pk_column(
            model=model, columns=columns, use_alias=use_alias
        )

        return columns
