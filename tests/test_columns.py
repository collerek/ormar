import datetime

import databases
import pytest
import sqlalchemy

import orm
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


def time():
    return datetime.datetime.now().time()


class Example(orm.Model):
    __tablename__ = "example"
    __metadata__ = metadata
    __database__ = database

    id = orm.Integer(primary_key=True)
    created = orm.DateTime(default=datetime.datetime.now)
    created_day = orm.Date(default=datetime.date.today)
    created_time = orm.Time(default=time)
    description = orm.Text(nullable=True)
    value = orm.Float(nullable=True)
    data = orm.JSON(default={})


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_model_crud():
    async with database:
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
