import databases
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Factory(ormar.Model):
    class Meta:
        tablename = "factories"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Toy(ormar.Model):
    class Meta:
        tablename = "toys"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    factory: Factory = ormar.ForeignKey(Factory)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_sort_order_on_main_model():
    async with database:
        factory = await Factory(name="Factory 1").save()

        toy1 = Toy(name="Bear", factory=factory)
        toy2 = Toy(name="Car", factory={"id": factory.id, "name": "Factory 1"})

        await Toy.objects.bulk_create([toy1, toy2])

        check = await Toy.objects.select_related(Toy.factory).all()
        assert check[0].factory == factory
        assert check[1].factory == factory
