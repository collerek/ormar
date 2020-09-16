import datetime
import os

import databases
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

assert "TEST_DATABASE_URLS" in os.environ, "TEST_DATABASE_URLS is not set."

DATABASE_URLS = [url.strip() for url in os.environ["TEST_DATABASE_URLS"].split(",")]

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


def time():
    return datetime.datetime.now().time()


class Example(ormar.Model):
    class Meta:
        tablename = "example"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    name: ormar.String(max_length=200, default="aaa")
    created: ormar.DateTime(default=datetime.datetime.now)
    created_day: ormar.Date(default=datetime.date.today)
    created_time: ormar.Time(default=time)
    description: ormar.Text(nullable=True)
    value: ormar.Float(nullable=True)
    data: ormar.JSON(default={})


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    for url in DATABASE_URLS:
        database_url = databases.DatabaseURL(url)
        if database_url.scheme == "mysql":
            url = str(database_url.replace(driver="pymysql"))
        elif database_url.scheme == "postgresql+aiopg":
            url = str(database_url.replace(driver=None))
        engine = sqlalchemy.create_engine(url)
        metadata.create_all(engine)

    yield
    for url in DATABASE_URLS:
        database_url = databases.DatabaseURL(url)
        if database_url.scheme == "mysql":
            url = str(database_url.replace(driver="pymysql"))
        elif database_url.scheme == "postgresql+aiopg":
            url = str(database_url.replace(driver=None))
        engine = sqlalchemy.create_engine(url)
        metadata.drop_all(engine)


@pytest.mark.parametrize("database_url", DATABASE_URLS)
@pytest.mark.asyncio
async def test_model_crud(database_url):
    async with databases.Database(database_url) as database:
        async with database.transaction(force_rollback=True):
            Example.Meta.database = database
            example = Example()
            await example.save()

            await example.load()
            assert example.created.year == datetime.datetime.now().year
            assert example.created_day == datetime.date.today()
            assert example.description is None
            assert example.value is None
            assert example.data == {}

            await example.update(data={"foo": 123}, value=123.456)
            await example.load()
            assert example.value == 123.456
            assert example.data == {"foo": 123}

            await example.delete()
