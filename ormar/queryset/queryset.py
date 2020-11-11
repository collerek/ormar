from typing import Any, List, Optional, Sequence, TYPE_CHECKING, Type, Union

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
    from ormar.models.metaclass import ModelMeta
    from ormar.relations.querysetproxy import QuerysetProxy


class QuerySet:
    def __init__(  # noqa CFQ002
        self,
        model_cls: Type["Model"] = None,
        filter_clauses: List = None,
        exclude_clauses: List = None,
        select_related: List = None,
        limit_count: int = None,
        offset: int = None,
        columns: List = None,
        exclude_columns: List = None,
        order_bys: List = None,
    ) -> None:
        self.model_cls = model_cls
        self.filter_clauses = [] if filter_clauses is None else filter_clauses
        self.exclude_clauses = [] if exclude_clauses is None else exclude_clauses
        self._select_related = [] if select_related is None else select_related
        self.limit_count = limit_count
        self.query_offset = offset
        self._columns = columns or []
        self._exclude_columns = exclude_columns or []
        self.order_bys = order_bys or []

    def __get__(
        self,
        instance: Optional[Union["QuerySet", "QuerysetProxy"]],
        owner: Union[Type["Model"], Type["QuerysetProxy"]],
    ) -> "QuerySet":
        if issubclass(owner, ormar.Model):
            return self.__class__(model_cls=owner)
        else:  # pragma nocover
            return self.__class__()

    @property
    def model_meta(self) -> "ModelMeta":
        if not self.model_cls:  # pragma nocover
            raise ValueError("Model class of QuerySet is not initialized")
        return self.model_cls.Meta

    @property
    def model(self) -> Type["Model"]:
        if not self.model_cls:  # pragma nocover
            raise ValueError("Model class of QuerySet is not initialized")
        return self.model_cls

    def _process_query_result_rows(self, rows: List) -> Sequence[Optional["Model"]]:
        result_rows = [
            self.model.from_row(
                row=row,
                select_related=self._select_related,
                fields=self._columns,
                exclude_fields=self._exclude_columns,
            )
            for row in rows
        ]
        if result_rows:
            return self.model.merge_instances_list(result_rows)  # type: ignore
        return result_rows

    def _prepare_model_to_save(self, new_kwargs: dict) -> dict:
        new_kwargs = self._remove_pk_from_kwargs(new_kwargs)
        new_kwargs = self.model.substitute_models_with_pks(new_kwargs)
        new_kwargs = self.model.populate_default_values(new_kwargs)
        new_kwargs = self.model.translate_columns_to_aliases(new_kwargs)
        return new_kwargs

    def _remove_pk_from_kwargs(self, new_kwargs: dict) -> dict:
        pkname = self.model_meta.pkname
        pk = self.model_meta.model_fields[pkname]
        if new_kwargs.get(pkname, ormar.Undefined) is None and (
            pk.nullable or pk.autoincrement
        ):
            del new_kwargs[pkname]
        return new_kwargs

    @staticmethod
    def check_single_result_rows_count(rows: Sequence[Optional["Model"]]) -> None:
        if not rows or rows[0] is None:
            raise NoMatch()
        if len(rows) > 1:
            raise MultipleMatches()

    @property
    def database(self) -> databases.Database:
        return self.model_meta.database

    @property
    def table(self) -> sqlalchemy.Table:
        return self.model_meta.table

    def build_select_expression(self) -> sqlalchemy.sql.select:
        qry = Query(
            model_cls=self.model,
            select_related=self._select_related,
            filter_clauses=self.filter_clauses,
            exclude_clauses=self.exclude_clauses,
            offset=self.query_offset,
            limit_count=self.limit_count,
            fields=self._columns,
            exclude_fields=self._exclude_columns,
            order_bys=self.order_bys,
        )
        exp = qry.build_select_expression()
        # print(exp.compile(compile_kwargs={"literal_binds": True}))
        return exp

    def filter(self, _exclude: bool = False, **kwargs: Any) -> "QuerySet":  # noqa: A003
        qryclause = QueryClause(
            model_cls=self.model,
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
            model_cls=self.model,
            filter_clauses=filter_clauses,
            exclude_clauses=exclude_clauses,
            select_related=select_related,
            limit_count=self.limit_count,
            offset=self.query_offset,
            columns=self._columns,
            exclude_columns=self._exclude_columns,
            order_bys=self.order_bys,
        )

    def exclude(self, **kwargs: Any) -> "QuerySet":  # noqa: A003
        return self.filter(_exclude=True, **kwargs)

    def select_related(self, related: Union[List, str]) -> "QuerySet":
        if not isinstance(related, list):
            related = [related]

        related = list(set(list(self._select_related) + related))
        return self.__class__(
            model_cls=self.model,
            filter_clauses=self.filter_clauses,
            exclude_clauses=self.exclude_clauses,
            select_related=related,
            limit_count=self.limit_count,
            offset=self.query_offset,
            columns=self._columns,
            exclude_columns=self._exclude_columns,
            order_bys=self.order_bys,
        )

    def exclude_fields(self, columns: Union[List, str]) -> "QuerySet":
        if not isinstance(columns, list):
            columns = [columns]

        columns = list(set(list(self._exclude_columns) + columns))
        return self.__class__(
            model_cls=self.model,
            filter_clauses=self.filter_clauses,
            exclude_clauses=self.exclude_clauses,
            select_related=self._select_related,
            limit_count=self.limit_count,
            offset=self.query_offset,
            columns=self._columns,
            exclude_columns=columns,
            order_bys=self.order_bys,
        )

    def fields(self, columns: Union[List, str]) -> "QuerySet":
        if not isinstance(columns, list):
            columns = [columns]

        columns = list(set(list(self._columns) + columns))
        return self.__class__(
            model_cls=self.model,
            filter_clauses=self.filter_clauses,
            exclude_clauses=self.exclude_clauses,
            select_related=self._select_related,
            limit_count=self.limit_count,
            offset=self.query_offset,
            columns=columns,
            exclude_columns=self._exclude_columns,
            order_bys=self.order_bys,
        )

    def order_by(self, columns: Union[List, str]) -> "QuerySet":
        if not isinstance(columns, list):
            columns = [columns]

        order_bys = self.order_bys + [x for x in columns if x not in self.order_bys]
        return self.__class__(
            model_cls=self.model,
            filter_clauses=self.filter_clauses,
            exclude_clauses=self.exclude_clauses,
            select_related=self._select_related,
            limit_count=self.limit_count,
            offset=self.query_offset,
            columns=self._columns,
            exclude_columns=self._exclude_columns,
            order_bys=order_bys,
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
        self_fields = self.model.extract_db_own_fields()
        updates = {k: v for k, v in kwargs.items() if k in self_fields}
        updates = self.model.translate_columns_to_aliases(updates)
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
            model_cls=self.model,
            filter_clauses=self.filter_clauses,
            exclude_clauses=self.exclude_clauses,
            select_related=self._select_related,
            limit_count=limit_count,
            offset=self.query_offset,
            columns=self._columns,
            exclude_columns=self._exclude_columns,
            order_bys=self.order_bys,
        )

    def offset(self, offset: int) -> "QuerySet":
        return self.__class__(
            model_cls=self.model,
            filter_clauses=self.filter_clauses,
            exclude_clauses=self.exclude_clauses,
            select_related=self._select_related,
            limit_count=self.limit_count,
            offset=offset,
            columns=self._columns,
            exclude_columns=self._exclude_columns,
            order_bys=self.order_bys,
        )

    async def first(self, **kwargs: Any) -> "Model":
        if kwargs:
            return await self.filter(**kwargs).first()

        rows = await self.limit(1).all()
        self.check_single_result_rows_count(rows)
        return rows[0]  # type: ignore

    async def get(self, **kwargs: Any) -> "Model":
        if kwargs:
            return await self.filter(**kwargs).get()

        expr = self.build_select_expression()
        if not self.filter_clauses:
            expr = expr.limit(2)

        rows = await self.database.fetch_all(expr)
        processed_rows = self._process_query_result_rows(rows)
        self.check_single_result_rows_count(processed_rows)
        return processed_rows[0]  # type: ignore

    async def get_or_create(self, **kwargs: Any) -> "Model":
        try:
            return await self.get(**kwargs)
        except NoMatch:
            return await self.create(**kwargs)

    async def update_or_create(self, **kwargs: Any) -> "Model":
        pk_name = self.model_meta.pkname
        if "pk" in kwargs:
            kwargs[pk_name] = kwargs.pop("pk")
        if pk_name not in kwargs or kwargs.get(pk_name) is None:
            return await self.create(**kwargs)
        model = await self.get(pk=kwargs[pk_name])
        return await model.update(**kwargs)

    async def all(self, **kwargs: Any) -> Sequence[Optional["Model"]]:  # noqa: A003
        if kwargs:
            return await self.filter(**kwargs).all()

        expr = self.build_select_expression()
        rows = await self.database.fetch_all(expr)
        result_rows = self._process_query_result_rows(rows)

        return result_rows

    async def create(self, **kwargs: Any) -> "Model":

        new_kwargs = dict(**kwargs)
        new_kwargs = self._prepare_model_to_save(new_kwargs)

        expr = self.table.insert()
        expr = expr.values(**new_kwargs)

        instance = self.model(**kwargs)
        pk = await self.database.execute(expr)

        pk_name = self.model.get_column_alias(self.model_meta.pkname)
        if pk_name not in kwargs and pk_name in new_kwargs:
            instance.pk = new_kwargs[self.model_meta.pkname]
        if pk and isinstance(pk, self.model.pk_type()):
            instance.pk = pk

        # refresh server side defaults
        instance = await instance.load()

        return instance

    async def bulk_create(self, objects: List["Model"]) -> None:
        ready_objects = []
        for objt in objects:
            new_kwargs = objt.dict()
            new_kwargs = self._prepare_model_to_save(new_kwargs)
            ready_objects.append(new_kwargs)

        expr = self.table.insert()
        await self.database.execute_many(expr, ready_objects)

    async def bulk_update(
        self, objects: List["Model"], columns: List[str] = None
    ) -> None:
        ready_objects = []
        pk_name = self.model_meta.pkname
        if not columns:
            columns = list(
                self.model.extract_db_own_fields().union(
                    self.model.extract_related_names()
                )
            )

        if pk_name not in columns:
            columns.append(pk_name)

        columns = [self.model.get_column_alias(k) for k in columns]

        for objt in objects:
            new_kwargs = objt.dict()
            if pk_name not in new_kwargs or new_kwargs.get(pk_name) is None:
                raise QueryDefinitionError(
                    "You cannot update unsaved objects. "
                    f"{self.model.__name__} has to have {pk_name} filled."
                )
            new_kwargs = self.model.substitute_models_with_pks(new_kwargs)
            new_kwargs = self.model.translate_columns_to_aliases(new_kwargs)
            new_kwargs = {"new_" + k: v for k, v in new_kwargs.items() if k in columns}
            ready_objects.append(new_kwargs)

        pk_column = self.model_meta.table.c.get(self.model.get_column_alias(pk_name))
        pk_column_name = self.model.get_column_alias(pk_name)
        table_columns = [c.name for c in self.model_meta.table.c]
        expr = self.table.update().where(
            pk_column == bindparam("new_" + pk_column_name)
        )
        expr = expr.values(
            **{
                k: bindparam("new_" + k)
                for k in columns
                if k != pk_column_name and k in table_columns
            }
        )
        # databases bind params only where query is passed as string
        # otherwise it just passes all data to values and results in unconsumed columns
        expr = str(expr)
        await self.database.execute_many(expr, ready_objects)
