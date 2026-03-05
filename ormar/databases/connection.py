"""
DatabaseConnection module - provides async database connection management.
"""

from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any, AsyncIterator, Optional

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from ormar.databases.query_executor import QueryExecutor
from ormar.databases.transaction import Transaction

_transaction_connection: ContextVar[Optional[AsyncConnection]] = ContextVar(
    "_transaction_connection", default=None
)


class DatabaseConnection:
    """
    Wrapper around SQLAlchemy AsyncEngine that provides a databases-compatible API.
    """

    def __init__(self, url: str, **options: Any) -> None:
        """
        Initialize database connection.

        :param url: Database URL with an async driver (e.g., postgresql+asyncpg://)
        :param options: Additional engine options
        """
        self._force_rollback = options.pop("force_rollback", False)
        self._url = url
        # Set reasonable pool defaults if not provided
        if "pool_size" not in options:
            options["pool_size"] = 5
        if "max_overflow" not in options:
            options["max_overflow"] = 10
        self._options = options
        self._engine: Optional[AsyncEngine] = None

        self._global_transaction: Optional[Transaction] = None

    async def connect(self) -> None:
        """Connect to the database by creating the async engine."""
        if self._engine is None:
            self._engine = create_async_engine(self._url, **self._options)

            # Set up SQLite foreign keys pragma if using SQLite
            if self._engine.dialect.name == "sqlite":  # pragma: nocover

                @event.listens_for(self._engine.sync_engine, "connect")
                def set_sqlite_pragma(dbapi_conn: Any, connection_record: Any) -> None:
                    cursor = dbapi_conn.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()

            if self._force_rollback:
                assert self._global_transaction is None
                self._global_transaction = Transaction(
                    self, force_rollback=self._force_rollback
                )
                await self._global_transaction.__aenter__()

    async def disconnect(self) -> None:
        """
        Disconnect from the database and dispose of the engine.
        In case of force_rollback, also roll back the global transaction.
        """
        if self._engine is not None:
            if self._force_rollback:
                assert self._global_transaction is not None
                await self._global_transaction.__aexit__()
                self._global_transaction = None

            await self._engine.dispose()
            self._engine = None

    @property
    def is_connected(self) -> bool:
        """Check if the engine is connected."""
        return self._engine is not None

    @property
    def engine(self) -> AsyncEngine:
        """Get the async engine."""
        assert self._engine is not None, "DatabaseConnection not connected"
        return self._engine

    @property
    def dialect(self) -> Any:
        """Get the database dialect."""
        return self.engine.dialect

    @property
    def url(self) -> str:
        """Get the database URL."""
        return self._url

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[AsyncConnection]:
        """
        Get a connection from the pool.
        If inside a transaction, returns the transaction connection.
        """
        trans_conn = _transaction_connection.get()
        if trans_conn is not None:
            yield trans_conn
        else:
            async with self.engine.connect() as conn:
                yield conn

    def transaction(self, force_rollback: bool = False) -> Transaction:
        """
        Create a transaction context manager.

        :param force_rollback: If True, always rollback (used for testing)
        """
        return Transaction(self, force_rollback=force_rollback)

    @asynccontextmanager
    async def get_query_executor(self) -> AsyncIterator[QueryExecutor]:
        """
        Get connection, reusing transaction connection if in transaction.

        :return: QueryExecutor wrapping a connection
        :rtype: QueryExecutor
        """
        trans_conn = self.get_transaction_connection()
        if trans_conn is not None:
            # Inside a transaction - reuse the transaction's connection
            yield QueryExecutor(trans_conn)
        else:
            # Outside transaction: connect() + commit().
            async with self.engine.connect() as conn:
                yield QueryExecutor(conn)
                await conn.commit()

    def get_transaction_connection(self) -> Optional[AsyncConnection]:
        """Get the current transaction connection if in a transaction."""
        return _transaction_connection.get()

    def set_transaction_connection(self, conn: Optional[AsyncConnection]) -> None:
        """Set the current transaction connection."""
        _transaction_connection.set(conn)

    async def __aenter__(self) -> "DatabaseConnection":
        """Async context manager entry - connect to a database."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit - disconnect from database."""
        await self.disconnect()
