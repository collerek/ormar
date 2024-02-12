import sqlite3

import asyncpg  # type: ignore
import ormar.fields.constraints
import pytest

from tests.settings import create_config
from tests.lifespan import init_tests


base_ormar_config = create_config()


class Product(ormar.Model):
    ormar_config = base_ormar_config.copy(
        tablename="products",
        constraints=[
            ormar.fields.constraints.CheckColumns("inventory > buffer"),
        ],
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    company: str = ormar.String(max_length=200)
    inventory: int = ormar.Integer()
    buffer: int = ormar.Integer()


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_check_columns_exclude_mysql():
    if Product.ormar_config.database._backend._dialect.name != "mysql":
        async with base_ormar_config.database:  # pragma: no cover
            async with base_ormar_config.database.transaction(force_rollback=True):
                await Product.objects.create(
                    name="Mars", company="Nestle", inventory=100, buffer=10
                )

                with pytest.raises(
                    (
                        sqlite3.IntegrityError,
                        asyncpg.exceptions.CheckViolationError,
                    )
                ):
                    await Product.objects.create(
                        name="Cookies", company="Nestle", inventory=1, buffer=10
                    )
