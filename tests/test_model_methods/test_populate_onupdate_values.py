from datetime import datetime

import databases
import pytest
import sqlalchemy
from sqlalchemy import func

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    database = database
    metadata = metadata


class Task(ormar.Model):
    class Meta(BaseMeta):
        tablename = "tasks"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(
        max_length=255,
        on_update=lambda: "hello",
    )
    points: int = ormar.Integer(default=0, minimum=0, on_update=1)
    year = ormar.Integer(on_update=2, default=1)
    updated_at: datetime = ormar.DateTime(
        default=datetime.now, server_default=func.now(), on_update=datetime.now
    )


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_onupdate_use_setattr_to_update():
    async with database:
        t1 = await Task.objects.create(name="123")
        assert t1.name == "123"
        assert t1.points == 0
        assert t1.year == 1

        t2 = await Task.objects.get(name="123")
        t2.name = "hello"
        t2.year = 2024
        await t2.update()
        assert t2.name == "hello"
        assert t2.points == 1
        assert t2.year == 2024
        assert t2.updated_at > t1.updated_at


@pytest.mark.asyncio
async def test_onupdate_use_update_func_kwargs():
    async with database:
        t1 = await Task.objects.create(name="123")
        assert t1.name == "123"
        assert t1.points == 0
        assert t1.year == 1

        t2 = await Task.objects.get(name="123")
        await t2.update(name="hello")
        assert t2.name == "hello"
        assert t2.points == 1
        assert t2.year == 2
        assert t2.updated_at > t1.updated_at


@pytest.mark.asyncio
async def test_onupdate_use_update_func_columns():
    async with database:
        t1 = await Task.objects.create(name="123")
        assert t1.name == "123"
        assert t1.points == 0
        assert t1.year == 1

        t2 = await Task.objects.get(name="123")
        await t2.update(_columns=["year"], year=2024)
        assert t2.name == "hello"
        assert t2.points == 1
        assert t2.year == 2024
        assert t2.updated_at > t1.updated_at


@pytest.mark.asyncio
async def test_onupdate_queryset_update():
    async with database:
        t1 = await Task.objects.create(name="123")
        assert t1.name == "123"
        assert t1.points == 0
        assert t1.year == 1

        await Task.objects.filter(name="123").update(name="hello")
        t2 = await Task.objects.get(name="hello")
        assert t2.name == "hello"
        assert t2.points == 1
        assert t2.year == 2
        assert t2.updated_at > t1.updated_at


@pytest.mark.asyncio
async def test_onupdate_bulk_update():
    async with database:
        t1 = await Task.objects.create(name="123")
        assert t1.name == "123"
        assert t1.points == 0
        assert t1.year == 1

        t2 = await Task.objects.get(name="123")
        t2.name = "bulk_update"
        await Task.objects.bulk_update([t2])
        t3 = await Task.objects.get(name="bulk_update")
        assert t3.name == "bulk_update"
        assert t3.points == 1
        assert t3.year == 2
        assert t3.updated_at > t2.updated_at
