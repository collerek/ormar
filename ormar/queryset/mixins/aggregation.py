from typing import (
    Any,
    Callable,
    Generic,
    List,
    TYPE_CHECKING,
    Type,
    TypeVar,
    Union
)

import databases
import sqlalchemy

from ormar.exceptions import QueryDefinitionError
from ormar.queryset import SelectAction

if TYPE_CHECKING:  # pragma no cover
    from ormar.models import T
else:
    T = TypeVar("T", bound="Model")


class AggregationMixin(Generic[T]):
    """
    The mixin class include aggregation operation:
        max, min, sum, avg
    """
    if TYPE_CHECKING:  # pragma: nocover
        build_select_expression: Callable

    @property
    def model(self) -> Type["T"]:  # pragma: nocover
        raise NotImplementedError

    @property
    def database(self) -> databases.Database:  # pragma: nocover
        raise NotImplementedError

    async def _query_aggr_function(self, func_name: str, columns: List) -> Any:
        func = getattr(sqlalchemy.func, func_name)
        select_actions = [
            SelectAction(select_str=column, model_cls=self.model) for column in
            columns
        ]
        if func_name in ["sum", "avg"]:
            if any(not x.is_numeric for x in select_actions):
                raise QueryDefinitionError(
                    "You can use sum and svg only with" "numeric types of columns"
                )
        select_columns = [
            x.apply_func(func, use_label=True) for x in select_actions
        ]
        expr = self.build_select_expression().alias(f"subquery_for_{func_name}")
        expr = sqlalchemy.select(select_columns).select_from(expr)
        # print("\n", expr.compile(compile_kwargs={"literal_binds": True}))
        result = await self.database.fetch_one(expr)
        return dict(result) if len(result) > 1 else result[0]  # type: ignore

    async def max(self, columns: Union[str, List[str]]) -> Any:  # noqa: A003
        """
        Returns max value of columns for rows matching the given criteria
        (applied with `filter` and `exclude` if set before).

        :return: max value of column(s)
        :rtype: Any
        """
        if not isinstance(columns, list):
            columns = [columns]
        return await self._query_aggr_function(func_name="max", columns=columns)

    async def min(self, columns: Union[str, List[str]]) -> Any:  # noqa: A003
        """
        Returns min value of columns for rows matching the given criteria
        (applied with `filter` and `exclude` if set before).

        :return: min value of column(s)
        :rtype: Any
        """
        if not isinstance(columns, list):
            columns = [columns]
        return await self._query_aggr_function(func_name="min", columns=columns)

    async def sum(self, columns: Union[str, List[str]]) -> Any:  # noqa: A003
        """
        Returns sum value of columns for rows matching the given criteria
        (applied with `filter` and `exclude` if set before).

        :return: sum value of columns
        :rtype: int
        """
        if not isinstance(columns, list):
            columns = [columns]
        return await self._query_aggr_function(func_name="sum", columns=columns)

    async def avg(self, columns: Union[str, List[str]]) -> Any:
        """
        Returns avg value of columns for rows matching the given criteria
        (applied with `filter` and `exclude` if set before).

        :return: avg value of columns
        :rtype: Union[int, float, List]
        """
        if not isinstance(columns, list):
            columns = [columns]
        return await self._query_aggr_function(func_name="avg", columns=columns)
