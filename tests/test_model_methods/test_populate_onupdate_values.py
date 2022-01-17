import databases
import pytest
import sqlalchemy

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
        max_length=255, onupdate=lambda: "hello",
    )
    age: int = ormar.Integer()
    points: int = ormar.Integer(
        default=0, minimum=0, onupdate=1
    )
    year = ormar.Integer(onupdate=2, default=1)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_populate_onupdate_values():
    async with database:
        task = Task(name="123", age=1, points=1)
        await task.save()

        assert task.year == 1
        await task.update(age=2)

        t = await Task.objects.filter(age=2).first()
        assert t.name == "hello"
        assert t.points == 1
        assert t.year == 2


@pytest.mark.asyncio
async def test_bulk_update_populate_onupdate_values():
    async with database:
        task1 = await Task(name="123", age=1, points=2).save()
        task2 = await Task(name="123", age=2, points=3).save()
        task3 = await Task(name="123", age=3, points=4).save()

        tasks = [task1, task2, task3]

        for task in tasks:
            task.age += 1

        await Task.objects.bulk_update(tasks)

        for task in await Task.objects.all():
            assert task.points == 1
            assert task.name == "hello"
            assert task.year == 2
