import pytest
import sqlalchemy

from contextlib import asynccontextmanager
from fastapi import FastAPI
from typing import AsyncIterator


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
    @pytest.fixture(autouse=True, scope=scope)
    def create_database():
        config.engine = sqlalchemy.create_engine(config.database.url._url)
        config.metadata.create_all(config.engine)

        yield

        config.metadata.drop_all(config.engine)

    return create_database
