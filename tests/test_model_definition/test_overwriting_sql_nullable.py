import sqlite3
from typing import Optional

import asyncpg
import databases
import pymysql
import sqlalchemy
from sqlalchemy import create_engine, text

import ormar
import pytest

from tests.settings import DATABASE_URL

db = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = db


class PrimaryModel(ormar.Model):
    class Meta(BaseMeta):
        tablename = "primary_models"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=255, index=True)
    some_text: Optional[str] = ormar.Text(nullable=True, sql_nullable=False)
    some_other_text: Optional[str] = ormar.String(
        max_length=255, nullable=True, sql_nullable=False, server_default=text("''")
    )


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_create_models():
    async with db:
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
