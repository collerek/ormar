import pytest

import databases
import ormar
import sqlalchemy

from tests.settings import DATABASE_URL


database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class ToDo(ormar.Model):
    class Meta:
        tablename = "todos"
        metadata = metadata
        database = database
        debug = True

    id: int = ormar.Integer(primary_key=True)


class Book(ormar.Model):
    class Meta:
        tablename = "book"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_debug_sql(capfd):
    async with database:
        await ToDo.objects.get_or_none(id=1)
        out, _ = capfd.readouterr()
        assert out

        await Book.objects.get_or_none(id=1)
        out, _ = capfd.readouterr()
        assert not out
