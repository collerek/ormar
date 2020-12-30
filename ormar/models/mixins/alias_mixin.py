from typing import Dict, List, Optional, Set, TYPE_CHECKING, Type, Union


class AliasMixin:
    if TYPE_CHECKING:  # pragma: no cover
        from ormar import Model, ModelMeta

        Meta: ModelMeta

    @classmethod
    def get_column_alias(cls, field_name: str) -> str:
        field = cls.Meta.model_fields.get(field_name)
        return field.get_alias() if field is not None else field_name

    @classmethod
    def get_column_name_from_alias(cls, alias: str) -> str:
        for field_name, field in cls.Meta.model_fields.items():
            if field.get_alias() == alias:
                return field_name
        return alias  # if not found it's not an alias but actual name

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

    @staticmethod
    def _populate_pk_column(
        model: Type["Model"], columns: List[str], use_alias: bool = False,
    ) -> List[str]:
        pk_alias = (
            model.get_column_alias(model.Meta.pkname)
            if use_alias
            else model.Meta.pkname
        )
        if pk_alias not in columns:
            columns.append(pk_alias)
        return columns

    @classmethod
    def own_table_columns(
        cls,
        model: Type["Model"],
        fields: Optional[Union[Set, Dict]],
        exclude_fields: Optional[Union[Set, Dict]],
        use_alias: bool = False,
    ) -> List[str]:
        columns = [
            model.get_column_name_from_alias(col.name) if not use_alias else col.name
            for col in model.Meta.table.columns
        ]
        field_names = [
            model.get_column_name_from_alias(col.name)
            for col in model.Meta.table.columns
        ]
        if fields:
            columns = [
                col
                for col, name in zip(columns, field_names)
                if model.is_included(fields, name)
            ]
        if exclude_fields:
            columns = [
                col
                for col, name in zip(columns, field_names)
                if not model.is_excluded(exclude_fields, name)
            ]

        # always has to return pk column for ormar to work
        columns = cls._populate_pk_column(
            model=model, columns=columns, use_alias=use_alias
        )

        return columns
