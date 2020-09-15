from typing import Any, List, Mapping, TYPE_CHECKING, Tuple, Type, Union

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

    def _process_query_result_rows(self, rows: List[Mapping]) -> List["Model"]:
        result_rows = [
            self.model_cls.from_row(row, select_related=self._select_related)
            for row in rows
        ]
        rows = self.model_cls.merge_instances_list(result_rows)
        return rows

    def _remove_pk_from_kwargs(self, new_kwargs: dict) -> dict:
        pkname = self.model_cls.Meta.pkname
        pk = self.model_cls.Meta.model_fields[pkname]
        if new_kwargs.get(pkname, ormar.Undefined) is None and (
            pk.nullable or pk.autoincrement
        ):
            del new_kwargs[pkname]
        return new_kwargs

    @staticmethod
    def check_single_result_rows_count(rows: List["Model"]) -> None:
        if not rows:
            raise NoMatch()
        if len(rows) > 1:
            raise MultipleMatches()

    @property
    def database(self) -> databases.Database:
        return self.model_cls.Meta.database

    @property
    def table(self) -> sqlalchemy.Table:
        return self.model_cls.Meta.table

    def build_select_expression(self) -> sqlalchemy.sql.select:
        qry = Query(
            model_cls=self.model_cls,
            select_related=self._select_related,
            filter_clauses=self.filter_clauses,
            offset=self.query_offset,
            limit_count=self.limit_count,
        )
        exp = qry.build_select_expression()
        # print(exp.compile(compile_kwargs={"literal_binds": True}))
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

        related = list(set(list(self._select_related) + related))
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
        # print(expr.compile(compile_kwargs={"literal_binds": True}))
        return await self.database.fetch_val(expr)

    async def count(self) -> int:
        expr = self.build_select_expression().alias("subquery_for_count")
        expr = sqlalchemy.func.count().select().select_from(expr)
        # print(expr.compile(compile_kwargs={"literal_binds": True}))
        return await self.database.fetch_val(expr)

    async def delete(self, **kwargs: Any) -> int:
        if kwargs:
            return await self.filter(**kwargs).delete()
        qry = Query(
            model_cls=self.model_cls,
            select_related=self._select_related,
            filter_clauses=self.filter_clauses,
            offset=self.query_offset,
            limit_count=self.limit_count,
        )
        expr = qry.filter(self.table.delete())
        return await self.database.execute(expr)

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
        self.check_single_result_rows_count(rows)
        return rows[0]

    async def get(self, **kwargs: Any) -> "Model":
        if kwargs:
            return await self.filter(**kwargs).get()

        expr = self.build_select_expression()
        if not self.filter_clauses:
            expr = expr.limit(2)

        rows = await self.database.fetch_all(expr)
        rows = self._process_query_result_rows(rows)
        self.check_single_result_rows_count(rows)
        return rows[0]

    async def all(self, **kwargs: Any) -> List["Model"]:  # noqa: A003
        if kwargs:
            return await self.filter(**kwargs).all()

        expr = self.build_select_expression()
        rows = await self.database.fetch_all(expr)
        result_rows = self._process_query_result_rows(rows)

        return result_rows

    async def create(self, **kwargs: Any) -> "Model":

        new_kwargs = dict(**kwargs)
        new_kwargs = self._remove_pk_from_kwargs(new_kwargs)
        new_kwargs = self.model_cls.substitute_models_with_pks(new_kwargs)

        expr = self.table.insert()
        expr = expr.values(**new_kwargs)

        # Execute the insert, and return a new model instance.
        instance = self.model_cls(**kwargs)
        pk = await self.database.execute(expr)
        setattr(instance, self.model_cls.Meta.pkname, pk)
        return instance
