from contextlib import asynccontextmanager
from typing import AsyncIterator

import pytest_asyncio
import sqlalchemy
from fastapi import FastAPI
from ormar import OrmarConfig
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tests.settings import ASYNC_DATABASE_URL


def lifespan(config):
    @asynccontextmanager
    async def do_lifespan(_: FastAPI) -> AsyncIterator[None]:
        if not config.database.is_connected:
            await config.database.connect()

        yield

        if config.database.is_connected:
            await config.database.disconnect()

    return do_lifespan


def drop_tables(
    connection: sqlalchemy.Connection, config: OrmarConfig
):  # pragma: no cover
    if connection.dialect.name == "postgresql":
        for table in reversed(config.metadata.sorted_tables):
            connection.execute(text(f'DROP TABLE IF EXISTS "{table.name}" CASCADE'))
    else:
        config.metadata.drop_all(connection)


def init_tests(config, scope="module"):
    @pytest_asyncio.fixture(autouse=True, scope=scope)
    async def create_database():

        # Drop and create tables in a single connection to avoid event loop issues
        async with config.engine.begin() as conn:

            def setup_tables(connection):  # pragma: no cover
                drop_tables(connection, config)
                config.metadata.create_all(connection)

            await conn.run_sync(setup_tables)

        # For PostgreSQL and MySQL, recreate engine to avoid event loop conflicts
        # asyncpg and aiomysql are strict about event loops
        if config.engine.dialect.name in ("postgresql", "mysql"):
            await config.engine.dispose()
            config._original_engine = config.engine
            config.engine = create_async_engine(ASYNC_DATABASE_URL)

        yield

        # Restore the original engine if it was swapped
        if hasattr(config, "_original_engine"):
            await config.engine.dispose()
            config.engine = config._original_engine
            delattr(config, "_original_engine")

        async with config.engine.begin() as conn:
            await conn.run_sync(drop_tables, config)

        await config.engine.dispose()

    return create_database
