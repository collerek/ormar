import copy
import inspect
import json
import uuid
from abc import ABCMeta
from typing import Any, List, Type
from typing import Set, Dict

import pydantic
import sqlalchemy
from pydantic import BaseConfig, create_model

from orm.exceptions import ModelDefinitionError, MultipleMatches, NoMatch
from orm.fields import BaseField
from orm.relations import RelationshipManager


def parse_pydantic_field_from_model_fields(object_dict: dict):
    pydantic_fields = {field_name: (
        base_field.__type__,
        ... if base_field.is_required else base_field.default_value
    )
        for field_name, base_field in object_dict.items()
        if isinstance(base_field, BaseField)}
    return pydantic_fields


FILTER_OPERATORS = {
    "exact": "__eq__",
    "iexact": "ilike",
    "contains": "like",
    "icontains": "ilike",
    "in": "in_",
    "gt": "__gt__",
    "gte": "__ge__",
    "lt": "__lt__",
    "lte": "__le__",
}


class QuerySet:
    ESCAPE_CHARACTERS = ['%', '_']

    def __init__(self, model_cls: Type['Model'] = None, filter_clauses: List = None, select_related: List = None,
                 limit_count: int = None, offset: int = None):
        self.model_cls = model_cls
        self.filter_clauses = [] if filter_clauses is None else filter_clauses
        self._select_related = [] if select_related is None else select_related
        self.limit_count = limit_count
        self.query_offset = offset

    def __get__(self, instance, owner):
        return self.__class__(model_cls=owner)

    @property
    def database(self):
        return self.model_cls.__database__

    @property
    def table(self):
        return self.model_cls.__table__

    def build_select_expression(self):
        tables = [self.table]
        select_from = self.table

        for item in self._select_related:
            model_cls = self.model_cls
            select_from = self.table
            for part in item.split("__"):
                model_cls = model_cls.__model_fields__[part].to
                select_from = sqlalchemy.sql.join(select_from, model_cls.__table__)
                tables.append(model_cls.__table__)

        expr = sqlalchemy.sql.select(tables)
        expr = expr.select_from(select_from)

        if self.filter_clauses:
            if len(self.filter_clauses) == 1:
                clause = self.filter_clauses[0]
            else:
                clause = sqlalchemy.sql.and_(*self.filter_clauses)
            expr = expr.where(clause)

        if self.limit_count:
            expr = expr.limit(self.limit_count)

        if self.query_offset:
            expr = expr.offset(self.query_offset)

        # print(expr.compile(compile_kwargs={"literal_binds": True}))
        return expr

    def filter(self, **kwargs):
        filter_clauses = self.filter_clauses
        select_related = list(self._select_related)

        if kwargs.get("pk"):
            pk_name = self.model_cls.__pkname__
            kwargs[pk_name] = kwargs.pop("pk")

        for key, value in kwargs.items():
            if "__" in key:
                parts = key.split("__")

                # Determine if we should treat the final part as a
                # filter operator or as a related field.
                if parts[-1] in FILTER_OPERATORS:
                    op = parts[-1]
                    field_name = parts[-2]
                    related_parts = parts[:-2]
                else:
                    op = "exact"
                    field_name = parts[-1]
                    related_parts = parts[:-1]

                model_cls = self.model_cls
                if related_parts:
                    # Add any implied select_related
                    related_str = "__".join(related_parts)
                    if related_str not in select_related:
                        select_related.append(related_str)

                    # Walk the relationships to the actual model class
                    # against which the comparison is being made.
                    for part in related_parts:
                        model_cls = model_cls.__model_fields__[part].to

                column = model_cls.__table__.columns[field_name]

            else:
                op = "exact"
                column = self.table.columns[key]

            # Map the operation code onto SQLAlchemy's ColumnElement
            # https://docs.sqlalchemy.org/en/latest/core/sqlelement.html#sqlalchemy.sql.expression.ColumnElement
            op_attr = FILTER_OPERATORS[op]
            has_escaped_character = False

            if op in ["contains", "icontains"]:
                has_escaped_character = any(c for c in self.ESCAPE_CHARACTERS
                                            if c in value)
                if has_escaped_character:
                    # enable escape modifier
                    for char in self.ESCAPE_CHARACTERS:
                        value = value.replace(char, f'\\{char}')
                value = f"%{value}%"

            if isinstance(value, Model):
                value = value.pk

            clause = getattr(column, op_attr)(value)
            clause.modifiers['escape'] = '\\' if has_escaped_character else None
            filter_clauses.append(clause)

        return self.__class__(
            model_cls=self.model_cls,
            filter_clauses=filter_clauses,
            select_related=select_related,
            limit_count=self.limit_count,
            offset=self.query_offset
        )

    def select_related(self, related):
        if not isinstance(related, (list, tuple)):
            related = [related]

        related = list(self._select_related) + related
        return self.__class__(
            model_cls=self.model_cls,
            filter_clauses=self.filter_clauses,
            select_related=related,
            limit_count=self.limit_count,
            offset=self.query_offset
        )

    async def exists(self) -> bool:
        expr = self.build_select_expression()
        expr = sqlalchemy.exists(expr).select()
        return await self.database.fetch_val(expr)

    async def count(self) -> int:
        expr = self.build_select_expression().alias("subquery_for_count")
        expr = sqlalchemy.func.count().select().select_from(expr)
        return await self.database.fetch_val(expr)

    def limit(self, limit_count: int):
        return self.__class__(
            model_cls=self.model_cls,
            filter_clauses=self.filter_clauses,
            select_related=self._select_related,
            limit_count=limit_count,
            offset=self.query_offset
        )

    def offset(self, offset: int):
        return self.__class__(
            model_cls=self.model_cls,
            filter_clauses=self.filter_clauses,
            select_related=self._select_related,
            limit_count=self.limit_count,
            offset=offset
        )

    async def first(self, **kwargs):
        if kwargs:
            return await self.filter(**kwargs).first()

        rows = await self.limit(1).all()
        if rows:
            return rows[0]

    async def get(self, **kwargs):
        if kwargs:
            return await self.filter(**kwargs).get()

        expr = self.build_select_expression().limit(2)
        rows = await self.database.fetch_all(expr)

        if not rows:
            raise NoMatch()
        if len(rows) > 1:
            raise MultipleMatches()
        return self.model_cls.from_row(rows[0], select_related=self._select_related)

    async def all(self, **kwargs):
        if kwargs:
            return await self.filter(**kwargs).all()

        expr = self.build_select_expression()
        rows = await self.database.fetch_all(expr)
        return [
            self.model_cls.from_row(row, select_related=self._select_related)
            for row in rows
        ]

    async def create(self, **kwargs):

        new_kwargs = dict(**kwargs)

        # Remove primary key when None to prevent not null constraint in postgresql.
        pkname = self.model_cls.__pkname__
        pk = self.model_cls.__model_fields__[pkname]
        if pkname in new_kwargs and new_kwargs.get(pkname) is None and (pk.nullable or pk.autoincrement):
            del new_kwargs[pkname]

        # substitute related models with their pk
        for field in self.model_cls.extract_related_names():
            if field in new_kwargs and new_kwargs.get(field) is not None:
                new_kwargs[field] = getattr(new_kwargs.get(field), self.model_cls.__model_fields__[field].to.__pkname__)

        # Build the insert expression.
        expr = self.table.insert()
        expr = expr.values(**new_kwargs)

        # Execute the insert, and return a new model instance.
        instance = self.model_cls(**kwargs)
        instance.pk = await self.database.execute(expr)
        return instance


class ModelMetaclass(type):
    def __new__(
            mcs: type, name: str, bases: Any, attrs: dict
    ) -> type:
        new_model = super().__new__(  # type: ignore
            mcs, name, bases, attrs
        )

        if attrs.get("__abstract__"):
            return new_model

        tablename = attrs["__tablename__"]
        metadata = attrs["__metadata__"]
        pkname = None

        columns = []
        model_fields = {}
        for field_name, field in attrs.items():
            if isinstance(field, BaseField):
                model_fields[field_name] = field
                if not field.pydantic_only:
                    if field.primary_key:
                        pkname = field_name
                    columns.append(field.get_column(field_name))

        # sqlalchemy table creation
        attrs['__table__'] = sqlalchemy.Table(tablename, metadata, *columns)
        attrs['__columns__'] = columns
        attrs['__pkname__'] = pkname

        if not pkname:
            raise ModelDefinitionError('Table has to have a primary key.')

        # pydantic model creation
        pydantic_fields = parse_pydantic_field_from_model_fields(attrs)
        config = type('Config', (BaseConfig,), {'orm_mode': True})
        pydantic_model = create_model(name, __config__=config, **pydantic_fields)
        attrs['__pydantic_fields__'] = pydantic_fields
        attrs['__pydantic_model__'] = pydantic_model
        attrs['__fields__'] = copy.deepcopy(pydantic_model.__fields__)
        attrs['__signature__'] = copy.deepcopy(pydantic_model.__signature__)
        attrs['__annotations__'] = copy.deepcopy(pydantic_model.__annotations__)
        attrs['__model_fields__'] = model_fields

        new_model = super().__new__(  # type: ignore
            mcs, name, bases, attrs
        )

        return new_model


class Model(tuple, metaclass=ModelMetaclass):
    __abstract__ = True

    objects = QuerySet()

    def __init__(self, *args, **kwargs) -> None:
        self._orm_id = uuid.uuid4().hex
        self._orm_saved = False
        self._orm_relationship_manager = RelationshipManager(self)
        self._orm_observers = []

        if "pk" in kwargs:
            kwargs[self.__pkname__] = kwargs.pop("pk")
        kwargs = {k: self.__model_fields__[k].expand_relationship(v, self) for k, v in kwargs.items()}
        self.values = self.__pydantic_model__(**kwargs)

    def __setattr__(self, key: str, value: Any) -> None:
        if key in self.__fields__:
            if self.is_conversion_to_json_needed(key) and not isinstance(value, str):
                try:
                    value = json.dumps(value)
                except TypeError:  # pragma no cover
                    pass
            value = self.__model_fields__[key].expand_relationship(value, self)
            setattr(self.values, key, value)
        else:
            super().__setattr__(key, value)

    def __getattribute__(self, key: str) -> Any:
        if key != '__fields__' and key in self.__fields__:
            if key in self._orm_relationship_manager:
                parent_item = self._orm_relationship_manager.get(key)
                return parent_item

            item = getattr(self.values, key, None)
            if item is not None and self.is_conversion_to_json_needed(key) and isinstance(item, str):
                try:
                    item = json.loads(item)
                except TypeError:  # pragma no cover
                    pass
            return item
        return super().__getattribute__(key)

    def __eq__(self, other):
        return self.values.dict() == other.values.dict()

    def __repr__(self):  # pragma no cover
        return self.values.__repr__()

    # def attach(self, observer: 'Model'):
    #     if all([obs._orm_id != observer._orm_id for obs in self._orm_observers]):
    #         self._orm_observers.append(observer)
    #
    # def detach(self, observer: 'Model'):
    #     for ind, obs in enumerate(self._orm_observers):
    #         if obs._orm_id == observer._orm_id:
    #             del self._orm_observers[ind]
    #             break
    #
    def notify(self):
        for obs in self._orm_observers:  # pragma no cover
            obs.orm_update(self)

    def orm_update(self, subject: 'Model') -> None:  # pragma no cover
        print('should be updated here')

    @classmethod
    def from_row(cls, row, select_related: List = None) -> 'Model':
        item = {}
        select_related = select_related or []
        for related in select_related:
            if "__" in related:
                first_part, remainder = related.split("__", 1)
                model_cls = cls.__model_fields__[first_part].to
                item[first_part] = model_cls.from_row(row, select_related=[remainder])
            else:
                model_cls = cls.__model_fields__[related].to
                item[related] = model_cls.from_row(row)

        for column in cls.__table__.columns:
            if column.name not in item:
                item[column.name] = row[column]

        return cls(**item)

    @classmethod
    def validate(cls: Type['Model'], value: Any) -> 'Model':  # pragma no cover
        return cls.__pydantic_model__.validate(cls.__pydantic_model__.__class__, value)

    @classmethod
    def __get_validators__(cls):  # pragma no cover
        yield cls.__pydantic_model__.validate

    @classmethod
    def schema(cls, by_alias: bool = True):  # pragma no cover
        return cls.__pydantic_model__.schame(cls.__pydantic_model__, by_alias=by_alias)

    def is_conversion_to_json_needed(self, column_name: str) -> bool:
        return self.__model_fields__.get(column_name).__type__ == pydantic.Json

    @property
    def pk(self):
        return getattr(self.values, self.__pkname__)

    @pk.setter
    def pk(self, value):
        setattr(self.values, self.__pkname__, value)

    @property
    def pk_column(self) -> sqlalchemy.Column:
        return self.__table__.primary_key.columns.values()[0]

    def dict(self) -> Dict:
        return self.values.dict()

    def from_dict(self, value_dict: Dict) -> None:
        for key, value in value_dict.items():
            setattr(self, key, value)

    def extract_own_model_fields(self) -> Dict:
        related_names = self.extract_related_names()
        self_fields = {k: v for k, v in self.dict().items() if k not in related_names}
        return self_fields

    @classmethod
    def extract_related_names(cls) -> Set:
        related_names = set()
        for name, field in cls.__fields__.items():
            if inspect.isclass(field.type_) and issubclass(field.type_, pydantic.BaseModel):
                related_names.add(name)
            # elif field.sub_fields and any(
            #         [inspect.isclass(f.type_) and issubclass(f.type_, pydantic.BaseModel) for f in field.sub_fields]):
            #     related_names.add(name)
        return related_names

    def extract_model_db_fields(self) -> Dict:
        self_fields = self.extract_own_model_fields()
        self_fields = {k: v for k, v in self_fields.items() if k in self.__table__.columns}
        for field in self.extract_related_names():
            if getattr(self, field) is not None:
                self_fields[field] = getattr(getattr(self, field), self.__model_fields__[field].to.__pkname__)
        return self_fields

    async def save(self) -> int:
        self_fields = self.extract_model_db_fields()
        if self.__model_fields__.get(self.__pkname__).autoincrement:
            self_fields.pop(self.__pkname__, None)
        expr = self.__table__.insert()
        expr = expr.values(**self_fields)
        item_id = await self.__database__.execute(expr)
        setattr(self, 'pk', item_id)
        self.notify()
        return item_id

    async def update(self, **kwargs: Any) -> int:
        if kwargs:
            new_values = {**self.dict(), **kwargs}
            self.from_dict(new_values)

        self_fields = self.extract_model_db_fields()
        self_fields.pop(self.__pkname__)
        expr = self.__table__.update().values(**self_fields).where(
            self.pk_column == getattr(self, self.__pkname__))
        result = await self.__database__.execute(expr)
        self.notify()
        return result

    async def delete(self) -> int:
        expr = self.__table__.delete()
        expr = expr.where(self.pk_column == (getattr(self, self.__pkname__)))
        result = await self.__database__.execute(expr)
        self.notify()
        return result

    async def load(self) -> 'Model':
        expr = self.__table__.select().where(self.pk_column == self.pk)
        row = await self.__database__.fetch_one(expr)
        self.from_dict(dict(row))
        self.notify()
        return self
