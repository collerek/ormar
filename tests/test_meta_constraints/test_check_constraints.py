import sqlite3

import asyncpg  # type: ignore
import databases
import pytest
import sqlalchemy

import ormar.fields.constraints
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Product(ormar.Model):
    class Meta:
        tablename = "products"
        metadata = metadata
        database = database
        constraints = [
            ormar.fields.constraints.CheckColumns("inventory > buffer"),
        ]

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    company: str = ormar.String(max_length=200)
    inventory: int = ormar.Integer()
    buffer: int = ormar.Integer()


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_check_columns_exclude_mysql():
    if Product.Meta.database._backend._dialect.name != "mysql":
        async with database:  # pragma: no cover
            async with database.transaction(force_rollback=True):
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
