from typing import Union

import ormar
import pytest
from ormar.exceptions import ModelPersistenceError

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Category(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="categories")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50, unique=True, index=True)
    code: int = ormar.Integer()


class Workshop(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="workshops")

    id: int = ormar.Integer(primary_key=True)
    topic: str = ormar.String(max_length=255, index=True)
    category: Union[ormar.Model, Category] = ormar.ForeignKey(
        Category, related_name="workshops", nullable=False
    )


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_model_relationship():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
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
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            cat = Category(name="Foo", code=123)
            with pytest.raises(ModelPersistenceError):
                await Workshop(topic="Topic 1", category=cat).save()

            with pytest.raises(ModelPersistenceError):
                await Workshop.objects.create(topic="Topic 1", category=cat)
