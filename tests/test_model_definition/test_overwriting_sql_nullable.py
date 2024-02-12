import sqlite3
from typing import Optional

import asyncpg
import ormar
import pymysql
import pytest
from sqlalchemy import text

from tests.settings import create_config
from tests.lifespan import init_tests


base_ormar_config = create_config()


class PrimaryModel(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="primary_models")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=255, index=True)
    some_text: Optional[str] = ormar.Text(nullable=True, sql_nullable=False)
    some_other_text: Optional[str] = ormar.String(
        max_length=255, nullable=True, sql_nullable=False, server_default=text("''")
    )


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_create_models():
    async with base_ormar_config.database:
        primary = await PrimaryModel(
            name="Foo", some_text="Bar", some_other_text="Baz"
        ).save()
        assert primary.id == 1

        primary2 = await PrimaryModel(name="Foo2", some_text="Bar2").save()
        assert primary2.id == 2

        with pytest.raises(
            (
                sqlite3.IntegrityError,
                pymysql.IntegrityError,
                asyncpg.exceptions.NotNullViolationError,
            )
        ):
            await PrimaryModel(name="Foo3").save()
