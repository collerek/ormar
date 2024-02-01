import sqlite3

import asyncpg  # type: ignore
import ormar.fields.constraints
import pymysql
import pytest

from tests.settings import create_config
from tests.lifespan import init_tests


base_ormar_config = create_config()


class Product(ormar.Model):
    ormar_config = base_ormar_config.copy(
        tablename="products",
        constraints=[ormar.fields.constraints.UniqueColumns("name", "company")],
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    company: str = ormar.String(max_length=200)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_unique_columns():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            await Product.objects.create(name="Cookies", company="Nestle")
            await Product.objects.create(name="Mars", company="Mars")
            await Product.objects.create(name="Mars", company="Nestle")

            with pytest.raises(
                (
                    sqlite3.IntegrityError,
                    pymysql.IntegrityError,
                    asyncpg.exceptions.UniqueViolationError,
                )
            ):
                await Product.objects.create(name="Mars", company="Mars")
