from typing import Any, List

import sqlalchemy

import ormar.queryset  # noqa I100
from ormar.models import FakePydantic  # noqa I100


class Model(FakePydantic):
    __abstract__ = False

    # objects = ormar.queryset.QuerySet()

    @classmethod
    def from_row(
        cls,
        row: sqlalchemy.engine.ResultProxy,
        select_related: List = None,
        previous_table: str = None,
    ) -> "Model":

        item = {}
        select_related = select_related or []

        table_prefix = cls.Meta._orm_relationship_manager.resolve_relation_join(
            previous_table, cls.Meta.table.name
        )
        previous_table = cls.Meta.table.name
        for related in select_related:
            if "__" in related:
                first_part, remainder = related.split("__", 1)
                model_cls = cls.Meta.model_fields[first_part].to
                child = model_cls.from_row(
                    row, select_related=[remainder], previous_table=previous_table
                )
                item[first_part] = child
            else:
                model_cls = cls.Meta.model_fields[related].to
                child = model_cls.from_row(row, previous_table=previous_table)
                item[related] = child

        for column in cls.Meta.table.columns:
            if column.name not in item:
                item[column.name] = row[
                    f'{table_prefix + "_" if table_prefix else ""}{column.name}'
                ]

        return cls(**item)

    async def save(self) -> "Model":
        self_fields = self._extract_model_db_fields()
        if self.Meta.model_fields.get(self.Meta.pkname).autoincrement:
            self_fields.pop(self.Meta.pkname, None)
        expr = self.Meta.table.insert()
        expr = expr.values(**self_fields)
        item_id = await self.Meta.database.execute(expr)
        setattr(self, self.Meta.pkname, item_id)
        return self

    async def update(self, **kwargs: Any) -> int:
        if kwargs:
            new_values = {**self.dict(), **kwargs}
            self.from_dict(new_values)

        self_fields = self._extract_model_db_fields()
        self_fields.pop(self.Meta.pkname)
        expr = (
            self.Meta.table.update()
            .values(**self_fields)
            .where(self.pk_column == getattr(self, self.Meta.pkname))
        )
        result = await self.Meta.database.execute(expr)
        return result

    async def delete(self) -> int:
        expr = self.Meta.table.delete()
        expr = expr.where(self.pk_column == (getattr(self, self.Meta.pkname)))
        result = await self.Meta.database.execute(expr)
        return result

    async def load(self) -> "Model":
        expr = self.Meta.table.select().where(self.pk_column == self.pk)
        row = await self.Meta.database.fetch_one(expr)
        self.from_dict(dict(row))
        return self
