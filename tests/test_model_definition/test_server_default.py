import asyncio
import time
from datetime import datetime

import databases
import pytest
import sqlalchemy
from sqlalchemy import func, text

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Product(ormar.Model):
    class Meta:
        tablename = "product"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    company: str = ormar.String(max_length=200, server_default="Acme")
    sort_order: int = ormar.Integer(server_default=text("10"))
    created: datetime = ormar.DateTime(server_default=func.now())


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


def test_table_defined_properly():
    assert Product.Meta.model_fields["created"].nullable
    assert not Product.__fields__["created"].required
    assert Product.Meta.table.columns["created"].server_default.arg.name == "now"


@pytest.mark.asyncio
async def test_model_creation():
    async with database:
        async with database.transaction(force_rollback=True):
            p1 = Product(name="Test")
            assert p1.created is None
            await p1.save()
            await p1.load()
            assert p1.created is not None
            assert p1.company == "Acme"
            assert p1.sort_order == 10

            date = datetime.strptime("2020-10-27 11:30", "%Y-%m-%d %H:%M")
            p3 = await Product.objects.create(
                name="Test2", created=date, company="Roadrunner", sort_order=1
            )
            assert p3.created is not None
            assert p3.created == date
            assert p1.created != p3.created
            assert p3.company == "Roadrunner"
            assert p3.sort_order == 1

            p3 = await Product.objects.get(name="Test2")
            assert p3.company == "Roadrunner"
            assert p3.sort_order == 1

            time.sleep(1)

            p2 = await Product.objects.create(name="Test3")
            assert p2.created is not None
            assert p2.company == "Acme"
            assert p2.sort_order == 10

            if Product.db_backend_name() != "postgresql":
                # postgres use transaction timestamp so it will remain the same
                assert p1.created != p2.created  # pragma nocover
