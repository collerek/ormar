from typing import List, TYPE_CHECKING

import sqlalchemy

import orm
from orm.exceptions import NoMatch, MultipleMatches

if TYPE_CHECKING:  # pragma no cover
    from orm.models import Model

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

    def __init__(self, model_cls: 'Model' = None, filter_clauses: List = None, select_related: List = None,
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

        print(expr.compile(compile_kwargs={"literal_binds": True}))
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

            if isinstance(value, orm.Model):
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
