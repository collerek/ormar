from contextlib import asynccontextmanager
from typing import AsyncIterator

import pytest_asyncio
from fastapi import FastAPI


def lifespan(config):
    @asynccontextmanager
    async def do_lifespan(_: FastAPI) -> AsyncIterator[None]:
        if not config.database.is_connected:
            await config.database.connect()

        yield

        if config.database.is_connected:
            await config.database.disconnect()

    return do_lifespan


def init_tests(config, scope="module"):
    @pytest_asyncio.fixture(autouse=True, scope=scope)
    async def create_database():
        # Use async engine for DDL operations
        async with config.engine.begin() as conn:
            await conn.run_sync(config.metadata.create_all)

        yield

        async with config.engine.begin() as conn:
            await conn.run_sync(config.metadata.drop_all)

    return create_database
