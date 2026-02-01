from contextlib import asynccontextmanager
from typing import AsyncIterator

import pytest
import sqlalchemy
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
    @pytest.fixture(autouse=True, scope=scope)
    def create_database():

        engine = sqlalchemy.create_engine(config.database.url._url)

        # Собираем все уникальные схемы, которые указаны в моделях
        schemas = set()
        for table in config.metadata.tables.values():
            if table.schema:
                schemas.add(table.schema)

        # Создаем схемы
        with engine.begin() as conn:
            for schema in schemas:
                conn.execute(sqlalchemy.text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))

        config.engine = engine
        config.metadata.create_all(config.engine)

        yield

        config.metadata.drop_all(config.engine)

        with engine.begin() as conn:
            for schema in schemas:
                conn.execute(sqlalchemy.text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
    
    return create_database
