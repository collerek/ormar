import asyncio
import sqlite3

import asyncpg
import databases
import pymysql
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Product(ormar.Model):
    class Meta:
        tablename = "products"
        metadata = metadata
        database = database
        constraints = [ormar.UniqueColumns("name", "company")]

    id: ormar.Integer(primary_key=True)
    name: ormar.String(max_length=100)
    company: ormar.String(max_length=200)


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="module")
async def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_unique_columns():
    async with database:
        async with database.transaction(force_rollback=True):
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
