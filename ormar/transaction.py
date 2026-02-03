"""
Transaction module - provides transaction management with savepoint support.
"""

from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncTransaction

if TYPE_CHECKING:
    from ormar.connection import DatabaseConnection

_transaction_depth: ContextVar[int] = ContextVar("_transaction_depth", default=0)


class Transaction:
    """
    Transaction context manager with support for nested transactions via savepoints.
    """

    def __init__(
        self, database: "DatabaseConnection", force_rollback: bool = False
    ) -> None:
        """
        Initialize transaction.

        :param database: DatabaseConnection instance
        :param force_rollback: If True, always rollback (used for testing)
        """
        self._database = database
        self._force_rollback = force_rollback
        self._connection: Optional[AsyncConnection] = None
        self._transaction: Optional[AsyncTransaction] = None
        self._depth: int = 0

    async def __aenter__(self) -> "Transaction":
        """Enter transaction context."""
        # Get current transaction depth
        self._depth = _transaction_depth.get()

        # If this is the outermost transaction, get a new connection
        if self._depth == 0:
            self._connection = await self._database.engine.connect().__aenter__()
            self._database.set_transaction_connection(self._connection)
            self._transaction = await self._connection.begin()
        else:
            # Nested transaction - use savepoint
            self._connection = self._database.get_transaction_connection()
            if self._connection is None:
                raise RuntimeError(
                    "No transaction connection available for nested transaction"
                )
            self._transaction = await self._connection.begin_nested()

        # Increment transaction depth
        _transaction_depth.set(self._depth + 1)

        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit transaction context."""
        try:
            # Decrement transaction depth
            _transaction_depth.set(self._depth)

            # Handle transaction completion
            if self._transaction is not None:
                if exc_type is not None or self._force_rollback:
                    # Rollback on exception or if force_rollback is True
                    await self._transaction.rollback()
                else:
                    # Commit if no exception and not force_rollback
                    await self._transaction.commit()
        finally:
            # Clean up outermost transaction
            if self._depth == 0:
                self._database.set_transaction_connection(None)
                if self._connection is not None:
                    await self._connection.close()
