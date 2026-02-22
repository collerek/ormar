from typing import Optional

import ormar
import pytest

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Category(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="categories")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Item(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="items")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    price: float = ormar.Float(default=0)
    category: Optional[Category] = ormar.ForeignKey(Category, nullable=True)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_arbitrary_sql_execution():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            if not await Item.objects.count():
                cat = await Category.objects.create(name="Electronics")
                await Item.objects.create(name="Tablet", price=449.99, category=cat)
                await Item.objects.create(name="Monitor", price=329.99, category=cat)

            column = "1 + 1"
            with pytest.raises(ormar.exceptions.QueryDefinitionError):
                await Item.objects.min(column)


@pytest.mark.asyncio
async def test_arbitrary_sql_execution_on_related_model():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            if not await Item.objects.count():
                cat = await Category.objects.create(name="Electronics")
                await Item.objects.create(name="Tablet", price=449.99, category=cat)
                await Item.objects.create(name="Monitor", price=329.99, category=cat)

            column = "category__1 + 1"
            with pytest.raises(ormar.exceptions.QueryDefinitionError):
                await Item.objects.min(column)


@pytest.mark.asyncio
async def test_schema_extraction():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            if not await Item.objects.count():
                cat = await Category.objects.create(name="Electronics")
                await Item.objects.create(name="Laptop", price=999.99, category=cat)

            column = "(SELECT GROUP_CONCAT(name) FROM sqlite_master WHERE type='table')"
            with pytest.raises(ormar.exceptions.QueryDefinitionError):
                await Item.objects.min(column)
