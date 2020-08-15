from typing import Any, List, TYPE_CHECKING, Tuple, Type, Union

import databases
import sqlalchemy

import ormar  # noqa I100
from ormar import MultipleMatches, NoMatch
from ormar.queryset.clause import QueryClause
from ormar.queryset.query import Query

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


class QuerySet:
    def __init__(
        self,
        model_cls: Type["Model"] = None,
        filter_clauses: List = None,
        select_related: List = None,
        limit_count: int = None,
        offset: int = None,
    ) -> None:
        self.model_cls = model_cls
        self.filter_clauses = [] if filter_clauses is None else filter_clauses
        self._select_related = [] if select_related is None else select_related
        self.limit_count = limit_count
        self.query_offset = offset
        self.order_bys = None

    def __get__(self, instance: "QuerySet", owner: Type["Model"]) -> "QuerySet":
        return self.__class__(model_cls=owner)

    @property
    def database(self) -> databases.Database:
        return self.model_cls.__database__

    @property
    def table(self) -> sqlalchemy.Table:
        return self.model_cls.__table__

    def build_select_expression(self) -> sqlalchemy.sql.select:
        qry = Query(
            model_cls=self.model_cls,
            select_related=self._select_related,
            filter_clauses=self.filter_clauses,
            offset=self.query_offset,
            limit_count=self.limit_count,
        )
        exp, self._select_related = qry.build_select_expression()
        return exp

    def filter(self, **kwargs: Any) -> "QuerySet":  # noqa: A003
        qryclause = QueryClause(
            model_cls=self.model_cls,
            select_related=self._select_related,
            filter_clauses=self.filter_clauses,
        )
        filter_clauses, select_related = qryclause.filter(**kwargs)

        return self.__class__(
            model_cls=self.model_cls,
            filter_clauses=filter_clauses,
            select_related=select_related,
            limit_count=self.limit_count,
            offset=self.query_offset,
        )

    def select_related(self, related: Union[List, Tuple, str]) -> "QuerySet":
        if not isinstance(related, (list, tuple)):
            related = [related]

        related = list(self._select_related) + related
        return self.__class__(
            model_cls=self.model_cls,
            filter_clauses=self.filter_clauses,
            select_related=related,
            limit_count=self.limit_count,
            offset=self.query_offset,
        )

    async def exists(self) -> bool:
        expr = self.build_select_expression()
        expr = sqlalchemy.exists(expr).select()
        return await self.database.fetch_val(expr)

    async def count(self) -> int:
        expr = self.build_select_expression().alias("subquery_for_count")
        expr = sqlalchemy.func.count().select().select_from(expr)
        return await self.database.fetch_val(expr)

    def limit(self, limit_count: int) -> "QuerySet":
        return self.__class__(
            model_cls=self.model_cls,
            filter_clauses=self.filter_clauses,
            select_related=self._select_related,
            limit_count=limit_count,
            offset=self.query_offset,
        )

    def offset(self, offset: int) -> "QuerySet":
        return self.__class__(
            model_cls=self.model_cls,
            filter_clauses=self.filter_clauses,
            select_related=self._select_related,
            limit_count=self.limit_count,
            offset=offset,
        )

    async def first(self, **kwargs: Any) -> "Model":
        if kwargs:
            return await self.filter(**kwargs).first()

        rows = await self.limit(1).all()
        if rows:
            return rows[0]

    async def get(self, **kwargs: Any) -> "Model":
        if kwargs:
            return await self.filter(**kwargs).get()

        expr = self.build_select_expression().limit(2)
        rows = await self.database.fetch_all(expr)

        if not rows:
            raise NoMatch()
        if len(rows) > 1:
            raise MultipleMatches()
        return self.model_cls.from_row(rows[0], select_related=self._select_related)

    async def all(self, **kwargs: Any) -> List["Model"]:  # noqa: A003
        if kwargs:
            return await self.filter(**kwargs).all()

        expr = self.build_select_expression()
        rows = await self.database.fetch_all(expr)
        result_rows = [
            self.model_cls.from_row(row, select_related=self._select_related)
            for row in rows
        ]

        result_rows = self.model_cls.merge_instances_list(result_rows)

        return result_rows

    async def create(self, **kwargs: Any) -> "Model":

        new_kwargs = dict(**kwargs)

        # Remove primary key when None to prevent not null constraint in postgresql.
        pkname = self.model_cls.__pkname__
        pk = self.model_cls.__model_fields__[pkname]
        if (
            pkname in new_kwargs
            and new_kwargs.get(pkname) is None
            and (pk.nullable or pk.autoincrement)
        ):
            del new_kwargs[pkname]

        # substitute related models with their pk
        for field in self.model_cls._extract_related_names():
            if field in new_kwargs and new_kwargs.get(field) is not None:
                if isinstance(new_kwargs.get(field), ormar.Model):
                    new_kwargs[field] = getattr(
                        new_kwargs.get(field),
                        self.model_cls.__model_fields__[field].to.__pkname__,
                    )
                else:
                    new_kwargs[field] = new_kwargs.get(field).get(
                        self.model_cls.__model_fields__[field].to.__pkname__
                    )

        # Build the insert expression.
        expr = self.table.insert()
        expr = expr.values(**new_kwargs)

        # Execute the insert, and return a new model instance.
        instance = self.model_cls(**kwargs)
        instance.pk = await self.database.execute(expr)
        return instance
