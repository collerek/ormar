from typing import List, TYPE_CHECKING, Type

import sqlalchemy
from sqlalchemy import text

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

    def __init__(self, model_cls: Type['Model'] = None, filter_clauses: List = None, select_related: List = None,
                 limit_count: int = None, offset: int = None):
        self.model_cls = model_cls
        self.filter_clauses = [] if filter_clauses is None else filter_clauses
        self._select_related = [] if select_related is None else select_related
        self.limit_count = limit_count
        self.query_offset = offset
        self.aliases_dict = dict()

    def __get__(self, instance, owner):
        return self.__class__(model_cls=owner)

    @property
    def database(self):
        return self.model_cls.__database__

    @property
    def table(self):
        return self.model_cls.__table__

    def prefixed_columns(self, alias, table):
        return [text(f'{alias}_{table.name}.{column.name} as {alias}_{column.name}')
                for column in table.columns]

    def prefixed_table_name(self, alias, name):
        return text(f'{name} {alias}_{name}')

    def on_clause(self, from_table, to_table, previous_alias, alias, to_key, from_key):
        return text(f'{alias}_{to_table}.{to_key}='
                    f'{previous_alias + "_" if previous_alias else ""}{from_table}.{from_key}')

    def build_select_expression(self):
        tables = [self.table]
        columns = list(self.table.columns)
        order_bys = [text(f'{self.table.name}.{self.model_cls.__pkname__}')]
        select_from = self.table

        for item in self._select_related:
            previous_alias = ''
            from_table = self.table.name
            prev_model = self.model_cls
            model_cls = self.model_cls

            for part in item.split("__"):

                model_cls = model_cls.__model_fields__[part].to
                to_table = model_cls.__table__.name

                alias = model_cls._orm_relationship_manager.resolve_relation_join(from_table, to_table)

                if prev_model.__model_fields__[part].virtual:
                    # TODO: change the key lookup
                    to_key = prev_model.__name__.lower()
                    from_key = model_cls.__pkname__
                else:
                    to_key = model_cls.__pkname__
                    from_key = part

                on_clause = self.on_clause(from_table, to_table, previous_alias, alias, to_key, from_key)
                target_table = self.prefixed_table_name(alias, to_table)
                select_from = sqlalchemy.sql.outerjoin(select_from, target_table, on_clause)
                tables.append(model_cls.__table__)
                order_bys.append(text(f'{alias}_{to_table}.{model_cls.__pkname__}'))
                columns.extend(self.prefixed_columns(alias, model_cls.__table__))

                previous_alias = alias
                from_table = to_table
                prev_model = model_cls

        expr = sqlalchemy.sql.select(columns)
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

        for order in order_bys:
            expr = expr.order_by(order)

        print(expr.compile(compile_kwargs={"literal_binds": True}))
        return expr

    def filter(self, **kwargs):
        filter_clauses = self.filter_clauses
        select_related = list(self._select_related)

        if kwargs.get("pk"):
            pk_name = self.model_cls.__pkname__
            kwargs[pk_name] = kwargs.pop("pk")

        for key, value in kwargs.items():
            table_prefix = ''
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
                    previous_table = model_cls.__tablename__
                    for part in related_parts:
                        current_table = model_cls.__model_fields__[part].to.__tablename__
                        table_prefix = model_cls._orm_relationship_manager.resolve_relation_join(previous_table,
                                                                                                 current_table)
                        model_cls = model_cls.__model_fields__[part].to
                        previous_table = current_table

                print(table_prefix)
                table = model_cls.__table__
                column = model_cls.__table__.columns[field_name]

            else:
                op = "exact"
                column = self.table.columns[key]
                table = self.table

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

            clause_text = str(clause.compile(compile_kwargs={"literal_binds": True}))
            alias = f'{table_prefix}_' if table_prefix else ''
            aliased_name = f'{alias}{table.name}.{column.name}'
            clause_text = clause_text.replace(f'{table.name}.{column.name}', aliased_name)
            clause = text(clause_text)

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
        result_rows = [
            self.model_cls.from_row(row, select_related=self._select_related)
            for row in rows
        ]

        result_rows = self.merge_result_rows(result_rows)

        return result_rows

    @classmethod
    def merge_result_rows(cls, result_rows):
        merged_rows = []
        for index, model in enumerate(result_rows):
            if index > 0 and model.pk == result_rows[index - 1].pk:
                result_rows[-1] = cls.merge_two_instances(model, merged_rows[-1])
            else:
                merged_rows.append(model)
        return merged_rows

    @classmethod
    def merge_two_instances(cls, one: 'Model', other: 'Model'):
        for field in one.__model_fields__.keys():
            print(field, one.dict(), other.dict())
            if isinstance(getattr(one, field), list) and not isinstance(getattr(one, field), orm.models.Model):
                setattr(other, field, getattr(one, field) + getattr(other, field))
            elif isinstance(getattr(one, field), orm.models.Model):
                if getattr(one, field).pk == getattr(other, field).pk:
                    setattr(other, field, cls.merge_two_instances(getattr(one, field), getattr(other, field)))
        return other

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
