import itertools
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Type, TypeVar

import sqlalchemy

import ormar.queryset  # noqa I100
from ormar.fields.many_to_many import ManyToManyField
from ormar.models import NewBaseModel  # noqa I100
from ormar.models.metaclass import ModelMeta


def group_related_list(list_: List) -> Dict:
    test_dict: Dict[str, Any] = dict()
    grouped = itertools.groupby(list_, key=lambda x: x.split("__")[0])
    for key, group in grouped:
        group_list = list(group)
        new = [
            "__".join(x.split("__")[1:]) for x in group_list if len(x.split("__")) > 1
        ]
        if any("__" in x for x in new):
            test_dict[key] = group_related_list(new)
        else:
            test_dict[key] = new
    return test_dict


if TYPE_CHECKING:  # pragma nocover
    from ormar import QuerySet

T = TypeVar("T", bound="Model")


class Model(NewBaseModel):
    __abstract__ = False
    if TYPE_CHECKING:  # pragma nocover
        Meta: ModelMeta
        objects: "QuerySet"

    def __repr__(self) -> str:  # pragma nocover
        _repr = {k: getattr(self, k) for k, v in self.Meta.model_fields.items()}
        return f"{self.__class__.__name__}({str(_repr)})"

    @classmethod
    def from_row(  # noqa CCR001
        cls: Type[T],
        row: sqlalchemy.engine.ResultProxy,
        select_related: List = None,
        related_models: Any = None,
        previous_table: str = None,
        fields: List = None,
        exclude_fields: List = None,
    ) -> Optional[T]:

        item: Dict[str, Any] = {}
        select_related = select_related or []
        related_models = related_models or []
        if select_related:
            related_models = group_related_list(select_related)

        if (
            previous_table
            and previous_table in cls.Meta.model_fields
            and issubclass(cls.Meta.model_fields[previous_table], ManyToManyField)
        ):
            previous_table = cls.Meta.model_fields[
                previous_table
            ].through.Meta.tablename

        if previous_table:
            table_prefix = cls.Meta.alias_manager.resolve_relation_join(
                previous_table, cls.Meta.table.name
            )
        else:
            table_prefix = ""
        previous_table = cls.Meta.table.name

        item = cls.populate_nested_models_from_row(
            item=item,
            row=row,
            related_models=related_models,
            previous_table=previous_table,
            fields=fields,
            exclude_fields=exclude_fields,
        )
        item = cls.extract_prefixed_table_columns(
            item=item,
            row=row,
            table_prefix=table_prefix,
            fields=fields,
            exclude_fields=exclude_fields,
            nested=table_prefix != "",
        )

        instance: Optional[T] = cls(**item) if item.get(
            cls.Meta.pkname, None
        ) is not None else None
        return instance

    @classmethod
    def populate_nested_models_from_row(  # noqa: CFQ002
        cls,
        item: dict,
        row: sqlalchemy.engine.ResultProxy,
        related_models: Any,
        previous_table: sqlalchemy.Table,
        fields: List = None,
        exclude_fields: List = None,
    ) -> dict:
        for related in related_models:
            if isinstance(related_models, dict) and related_models[related]:
                first_part, remainder = related, related_models[related]
                model_cls = cls.Meta.model_fields[first_part].to
                child = model_cls.from_row(
                    row,
                    related_models=remainder,
                    previous_table=previous_table,
                    fields=fields,
                    exclude_fields=exclude_fields,
                )
                item[model_cls.get_column_name_from_alias(first_part)] = child
            else:
                model_cls = cls.Meta.model_fields[related].to
                child = model_cls.from_row(
                    row,
                    previous_table=previous_table,
                    fields=fields,
                    exclude_fields=exclude_fields,
                )
                item[model_cls.get_column_name_from_alias(related)] = child

        return item

    @classmethod
    def extract_prefixed_table_columns(  # noqa CCR001
        cls,
        item: dict,
        row: sqlalchemy.engine.result.ResultProxy,
        table_prefix: str,
        fields: List = None,
        exclude_fields: List = None,
        nested: bool = False,
    ) -> dict:

        # databases does not keep aliases in Record for postgres, change to raw row
        source = row._row if cls.db_backend_name() == "postgresql" else row

        selected_columns = cls.own_table_columns(
            cls, fields or [], exclude_fields or [], nested=nested, use_alias=True
        )

        for column in cls.Meta.table.columns:
            alias = cls.get_column_name_from_alias(column.name)
            if alias not in item and alias in selected_columns:
                prefixed_name = (
                    f'{table_prefix + "_" if table_prefix else ""}{column.name}'
                )
                item[alias] = source[prefixed_name]

        return item

    async def save(self: T) -> T:
        self_fields = self._extract_model_db_fields()

        if not self.pk and self.Meta.model_fields[self.Meta.pkname].autoincrement:
            self_fields.pop(self.Meta.pkname, None)
        self_fields = self.populate_default_values(self_fields)

        self_fields = self.translate_columns_to_aliases(self_fields)
        expr = self.Meta.table.insert()
        expr = expr.values(**self_fields)

        item_id = await self.Meta.database.execute(expr)
        if item_id:  # postgress does not return id if it's already there
            setattr(self, self.Meta.pkname, item_id)
        return self

    async def update(self: T, **kwargs: Any) -> T:
        if kwargs:
            new_values = {**self.dict(), **kwargs}
            self.from_dict(new_values)

        self_fields = self._extract_model_db_fields()
        self_fields.pop(self.get_column_name_from_alias(self.Meta.pkname))
        self_fields = self.translate_columns_to_aliases(self_fields)
        expr = self.Meta.table.update().values(**self_fields)
        expr = expr.where(self.pk_column == getattr(self, self.Meta.pkname))

        await self.Meta.database.execute(expr)
        return self

    async def delete(self: T) -> int:
        expr = self.Meta.table.delete()
        expr = expr.where(self.pk_column == (getattr(self, self.Meta.pkname)))
        result = await self.Meta.database.execute(expr)
        return result

    async def load(self: T) -> T:
        expr = self.Meta.table.select().where(self.pk_column == self.pk)
        row = await self.Meta.database.fetch_one(expr)
        if not row:  # pragma nocover
            raise ValueError(
                "Instance was deleted from database and cannot be refreshed"
            )
        kwargs = dict(row)
        kwargs = self.translate_aliases_to_columns(kwargs)
        self.from_dict(kwargs)
        return self
