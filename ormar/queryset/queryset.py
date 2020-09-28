from typing import Any, List, Mapping, TYPE_CHECKING, Tuple, Type, Union

import databases
import sqlalchemy
from sqlalchemy import bindparam

import ormar  # noqa I100
from ormar import MultipleMatches, NoMatch
from ormar.exceptions import QueryDefinitionError
from ormar.queryset import FilterQuery
from ormar.queryset.clause import QueryClause
from ormar.queryset.query import Query

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


class QuerySet:
    def __init__(  # noqa CFQ002
        self,
        model_cls: Type["Model"] = None,
        filter_clauses: List = None,
        exclude_clauses: List = None,
        select_related: List = None,
        limit_count: int = None,
        offset: int = None,
    ) -> None:
        self.model_cls = model_cls
        self.filter_clauses = [] if filter_clauses is None else filter_clauses
        self.exclude_clauses = [] if exclude_clauses is None else exclude_clauses
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

    def _populate_default_values(self, new_kwargs: dict) -> dict:
        for field_name, field in self.model_cls.Meta.model_fields.items():
            if field_name not in new_kwargs and field.has_default():
                new_kwargs[field_name] = field.get_default()
        return new_kwargs

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
            exclude_clauses=self.exclude_clauses,
            offset=self.query_offset,
            limit_count=self.limit_count,
        )
        exp = qry.build_select_expression()
        # print(exp.compile(compile_kwargs={"literal_binds": True}))
        return exp

    def filter(self, _exclude: bool = False, **kwargs: Any) -> "QuerySet":  # noqa: A003
        qryclause = QueryClause(
            model_cls=self.model_cls,
            select_related=self._select_related,
            filter_clauses=self.filter_clauses,
        )
        filter_clauses, select_related = qryclause.filter(**kwargs)
        if _exclude:
            exclude_clauses = filter_clauses
            filter_clauses = self.filter_clauses
        else:
            exclude_clauses = self.exclude_clauses
            filter_clauses = filter_clauses

        return self.__class__(
            model_cls=self.model_cls,
            filter_clauses=filter_clauses,
            exclude_clauses=exclude_clauses,
            select_related=select_related,
            limit_count=self.limit_count,
            offset=self.query_offset,
        )

    def exclude(self, **kwargs: Any) -> "QuerySet":  # noqa: A003
        return self.filter(_exclude=True, **kwargs)

    def select_related(self, related: Union[List, Tuple, str]) -> "QuerySet":
        if not isinstance(related, (list, tuple)):
            related = [related]

        related = list(set(list(self._select_related) + related))
        return self.__class__(
            model_cls=self.model_cls,
            filter_clauses=self.filter_clauses,
            exclude_clauses=self.exclude_clauses,
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

    async def update(self, each: bool = False, **kwargs: Any) -> int:
        self_fields = self.model_cls.extract_db_own_fields()
        updates = {k: v for k, v in kwargs.items() if k in self_fields}
        if not each and not self.filter_clauses:
            raise QueryDefinitionError(
                "You cannot update without filtering the queryset first. "
                "If you want to update all rows use update(each=True, **kwargs)"
            )
        expr = FilterQuery(filter_clauses=self.filter_clauses).apply(
            self.table.update().values(**updates)
        )
        return await self.database.execute(expr)

    async def delete(self, each: bool = False, **kwargs: Any) -> int:
        if kwargs:
            return await self.filter(**kwargs).delete()
        if not each and not self.filter_clauses:
            raise QueryDefinitionError(
                "You cannot delete without filtering the queryset first. "
                "If you want to delete all rows use delete(each=True)"
            )
        expr = FilterQuery(filter_clauses=self.filter_clauses).apply(
            self.table.delete()
        )
        return await self.database.execute(expr)

    def limit(self, limit_count: int) -> "QuerySet":
        return self.__class__(
            model_cls=self.model_cls,
            filter_clauses=self.filter_clauses,
            exclude_clauses=self.exclude_clauses,
            select_related=self._select_related,
            limit_count=limit_count,
            offset=self.query_offset,
        )

    def offset(self, offset: int) -> "QuerySet":
        return self.__class__(
            model_cls=self.model_cls,
            filter_clauses=self.filter_clauses,
            exclude_clauses=self.exclude_clauses,
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

    async def get_or_create(self, **kwargs: Any) -> "Model":
        try:
            return await self.get(**kwargs)
        except NoMatch:
            return await self.create(**kwargs)

    async def update_or_create(self, **kwargs: Any) -> "Model":
        pk_name = self.model_cls.Meta.pkname
        if "pk" in kwargs:
            kwargs[pk_name] = kwargs.pop("pk")
        if pk_name not in kwargs or kwargs.get(pk_name) is None:
            return await self.create(**kwargs)
        model = await self.get(pk=kwargs[pk_name])
        return await model.update(**kwargs)

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
        new_kwargs = self._populate_default_values(new_kwargs)

        expr = self.table.insert()
        expr = expr.values(**new_kwargs)

        # Execute the insert, and return a new model instance.
        instance = self.model_cls(**kwargs)
        pk = await self.database.execute(expr)
        pk_name = self.model_cls.Meta.pkname
        if pk_name not in kwargs and pk_name in new_kwargs:
            instance.pk = new_kwargs[self.model_cls.Meta.pkname]
        if pk and isinstance(pk, self.model_cls.pk_type()):
            setattr(instance, self.model_cls.Meta.pkname, pk)
        return instance

    async def bulk_create(self, objects: List["Model"]) -> None:
        ready_objects = []
        for objt in objects:
            new_kwargs = objt.dict()
            new_kwargs = self._remove_pk_from_kwargs(new_kwargs)
            new_kwargs = self.model_cls.substitute_models_with_pks(new_kwargs)
            new_kwargs = self._populate_default_values(new_kwargs)
            ready_objects.append(new_kwargs)

        expr = self.table.insert()
        await self.database.execute_many(expr, ready_objects)

    async def bulk_update(
        self, objects: List["Model"], columns: List[str] = None
    ) -> None:
        ready_objects = []
        pk_name = self.model_cls.Meta.pkname
        if not columns:
            columns = self.model_cls.extract_db_own_fields().union(
                self.model_cls.extract_related_names()
            )

        if pk_name not in columns:
            columns.append(pk_name)

        for objt in objects:
            new_kwargs = objt.dict()
            if pk_name not in new_kwargs or new_kwargs.get(pk_name) is None:
                raise QueryDefinitionError(
                    "You cannot update unsaved objects. "
                    f"{self.model_cls.__name__} has to have {pk_name} filled."
                )
            new_kwargs = self.model_cls.substitute_models_with_pks(new_kwargs)
            new_kwargs = {"new_" + k: v for k, v in new_kwargs.items() if k in columns}
            ready_objects.append(new_kwargs)

        pk_column = self.model_cls.Meta.table.c.get(pk_name)
        expr = self.table.update().where(pk_column == bindparam("new_" + pk_name))
        expr = expr.values(
            **{k: bindparam("new_" + k) for k in columns if k != pk_name}
        )
        # databases bind params only where query is passed as string
        # otherwise it just pases all data to values and results in unconsumed columns
        expr = str(expr)
        await self.database.execute_many(expr, ready_objects)
