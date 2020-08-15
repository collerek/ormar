from typing import Any, List

import sqlalchemy

import ormar.queryset  # noqa I100
from ormar.models import FakePydantic  # noqa I100


class Model(FakePydantic):
    __abstract__ = True

    objects = ormar.queryset.QuerySet()

    @classmethod
    def from_row(
        cls,
        row: sqlalchemy.engine.ResultProxy,
        select_related: List = None,
        previous_table: str = None,
    ) -> "Model":

        item = {}
        select_related = select_related or []

        table_prefix = cls._orm_relationship_manager.resolve_relation_join(
            previous_table, cls.__table__.name
        )
        previous_table = cls.__table__.name
        for related in select_related:
            if "__" in related:
                first_part, remainder = related.split("__", 1)
                model_cls = cls.__model_fields__[first_part].to
                child = model_cls.from_row(
                    row, select_related=[remainder], previous_table=previous_table
                )
                item[first_part] = child
            else:
                model_cls = cls.__model_fields__[related].to
                child = model_cls.from_row(row, previous_table=previous_table)
                item[related] = child

        for column in cls.__table__.columns:
            if column.name not in item:
                item[column.name] = row[
                    f'{table_prefix + "_" if table_prefix else ""}{column.name}'
                ]

        return cls(**item)

    @property
    def pk(self) -> str:
        return getattr(self.values, self.__pkname__)

    @pk.setter
    def pk(self, value: Any) -> None:
        setattr(self.values, self.__pkname__, value)

    async def save(self) -> "Model":
        self_fields = self._extract_model_db_fields()
        if self.__model_fields__.get(self.__pkname__).autoincrement:
            self_fields.pop(self.__pkname__, None)
        expr = self.__table__.insert()
        expr = expr.values(**self_fields)
        item_id = await self.__database__.execute(expr)
        self.pk = item_id
        return self

    async def update(self, **kwargs: Any) -> int:
        if kwargs:
            new_values = {**self.dict(), **kwargs}
            self.from_dict(new_values)

        self_fields = self._extract_model_db_fields()
        self_fields.pop(self.__pkname__)
        expr = (
            self.__table__.update()
            .values(**self_fields)
            .where(self.pk_column == getattr(self, self.__pkname__))
        )
        result = await self.__database__.execute(expr)
        return result

    async def delete(self) -> int:
        expr = self.__table__.delete()
        expr = expr.where(self.pk_column == (getattr(self, self.__pkname__)))
        result = await self.__database__.execute(expr)
        return result

    async def load(self) -> "Model":
        expr = self.__table__.select().where(self.pk_column == self.pk)
        row = await self.__database__.fetch_one(expr)
        self.from_dict(dict(row))
        return self
