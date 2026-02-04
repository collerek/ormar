"""
QueryExecutor module - executes database queries using SQLAlchemy async API.
"""

from typing import Any, AsyncIterator, List, Mapping, Optional, Sequence, Union

from sqlalchemy import RowMapping, text
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import Executable


class QueryExecutor:
    """
    Executes database queries using SQLAlchemy async API.
    Provides a databases-compatible interface.
    """

    def __init__(self, connection: AsyncConnection) -> None:
        """
        Initialize query executor.

        :param connection: SQLAlchemy async connection
        """
        self._connection = connection

    async def fetch_all(self, query: Executable) -> List[Any]:
        """
        Execute a query and fetch all rows.

        :param query: SQLAlchemy query expression
        :return: List of Row objects
        """
        result: CursorResult[Any] = await self._connection.execute(query)
        return list(result.mappings().all())

    async def fetch_one(self, query: Executable) -> Optional[RowMapping]:
        """
        Execute a query and fetch one row.

        :param query: SQLAlchemy query expression
        :return: Single Row object or None
        """
        result: CursorResult[Any] = await self._connection.execute(query)
        row = result.mappings().first()
        return row

    async def fetch_val(self, query: Executable, column: int = 0) -> Optional[Any]:
        """
        Execute a query and fetch a single scalar value.

        :param query: SQLAlchemy query expression
        :param column: Column index to fetch (default 0)
        :return: Scalar value or None
        """
        result: CursorResult[Any] = await self._connection.execute(query)
        return result.scalar()

    async def execute(self, query: Executable) -> Any:
        """
        Execute a query (INSERT, UPDATE, DELETE).

        :param query: SQLAlchemy query expression
        :return: For INSERT, returns last row id; for UPDATE/DELETE, returns row count
        """
        result: CursorResult[Any] = await self._connection.execute(query)

        # Don't commit - let connection context manager or transaction handle it

        # Return lastrowid for INSERT, rowcount for UPDATE/DELETE
        if hasattr(result, "lastrowid") and result.lastrowid:
            return result.lastrowid
        return result.rowcount if result.rowcount is not None else 0

    async def execute_many(
        self, query: Union[Executable, str], values: Sequence[Mapping[str, Any]]
    ) -> None:
        """
        Execute a query multiple times with different parameter sets.

        :param query: SQLAlchemy query expression or SQL string
        :param values: Sequence of parameter mappings
        """
        # Convert string queries to text() objects
        exec_query: Executable
        if isinstance(query, str):
            exec_query = text(query)
        else:
            exec_query = query

        # For bulk operations, execute multiple times
        for value_dict in values:
            await self._connection.execute(exec_query, value_dict)

        # Don't commit - let connection context manager or transaction handle it

    async def iterate(self, query: Executable) -> AsyncIterator[Any]:
        """
        Execute a query and iterate over results.

        :param query: SQLAlchemy query expression
        :return: Async iterator of Row objects
        """
        async with self._connection.stream(query) as result:
            async for row in result.mappings():
                yield row
