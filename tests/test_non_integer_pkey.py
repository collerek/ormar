import random

import databases
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


def key():
    return "".join(random.choice("abcdefgh123456") for _ in range(8))


class Model(ormar.Model):
    class Meta:
        tablename = "models"
        metadata = metadata
        database = database

    id: ormar.String(primary_key=True, default=key, max_length=8)
    name: ormar.String(max_length=32)


@pytest.fixture(autouse=True, scope="function")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_pk_1():
    async with database:
        model = await Model.objects.create(name="NAME")
        assert isinstance(model.id, str)


@pytest.mark.asyncio
async def test_pk_2():
    # async with database:
        model = await Model.objects.create(name="NAME")
        assert await Model.objects.all() == [model]