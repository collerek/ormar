from typing import Union

import databases
import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine

import ormar
from ormar.exceptions import ModelPersistenceError
from tests.settings import DATABASE_URL

metadata = sa.MetaData()
db = databases.Database(DATABASE_URL)


class Category(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename = "categories",
        metadata = metadata,
        database = db,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50, unique=True, index=True)
    code: int = ormar.Integer()


class Workshop(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename = "workshops",
        metadata = metadata,
        database = db,
    )

    id: int = ormar.Integer(primary_key=True)
    topic: str = ormar.String(max_length=255, index=True)
    category: Union[ormar.Model, Category] = ormar.ForeignKey(
        Category, related_name="workshops", nullable=False
    )


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_model_relationship():
    async with db:
        async with db.transaction(force_rollback=True):
            cat = await Category(name="Foo", code=123).save()
            ws = await Workshop(topic="Topic 1", category=cat).save()

            assert ws.id == 1
            assert ws.topic == "Topic 1"
            assert ws.category.name == "Foo"

            ws.topic = "Topic 2"
            await ws.update()

            assert ws.id == 1
            assert ws.topic == "Topic 2"
            assert ws.category.name == "Foo"


@pytest.mark.asyncio
async def test_model_relationship_with_not_saved():
    async with db:
        async with db.transaction(force_rollback=True):
            cat = Category(name="Foo", code=123)
            with pytest.raises(ModelPersistenceError):
                await Workshop(topic="Topic 1", category=cat).save()

            with pytest.raises(ModelPersistenceError):
                await Workshop.objects.create(topic="Topic 1", category=cat)
