from typing import List

import ormar
import pytest

from tests.settings import create_config
from tests.lifespan import init_tests


base_ormar_config = create_config()


class Category(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="categories")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, default="Test", nullable=True)
    visibility: bool = ormar.Boolean(default=True)


class Item(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="items")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    price: float = ormar.Float(default=9.99)
    categories: List[Category] = ormar.ManyToMany(Category)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_exclude_default():
    async with base_ormar_config.database:
        category = Category()
        assert category.model_dump() == {
            "id": None,
            "items": [],
            "name": "Test",
            "visibility": True,
        }
        assert category.model_dump(exclude_defaults=True) == {"items": []}

        await category.save()
        category2 = await Category.objects.get()
        assert category2.model_dump() == {
            "id": 1,
            "items": [],
            "name": "Test",
            "visibility": True,
        }
        assert category2.model_dump(exclude_defaults=True) == {"id": 1, "items": []}
        assert category2.model_dump_json(exclude_defaults=True) == '{"id":1,"items":[]}'


@pytest.mark.asyncio
async def test_exclude_none():
    async with base_ormar_config.database:
        category = Category(id=2, name=None)
        assert category.model_dump() == {
            "id": 2,
            "items": [],
            "name": None,
            "visibility": True,
        }
        assert category.model_dump(exclude_none=True) == {
            "id": 2,
            "items": [],
            "visibility": True,
        }

        await category.save()
        category2 = await Category.objects.get()
        assert category2.model_dump() == {
            "id": 2,
            "items": [],
            "name": None,
            "visibility": True,
        }
        assert category2.model_dump(exclude_none=True) == {
            "id": 2,
            "items": [],
            "visibility": True,
        }
        assert (
            category2.model_dump_json(exclude_none=True)
            == '{"id":2,"visibility":true,"items":[]}'
        )


@pytest.mark.asyncio
async def test_exclude_unset():
    async with base_ormar_config.database:
        category = Category(id=3, name="Test 2")
        assert category.model_dump() == {
            "id": 3,
            "items": [],
            "name": "Test 2",
            "visibility": True,
        }
        assert category.model_dump(exclude_unset=True) == {
            "id": 3,
            "items": [],
            "name": "Test 2",
        }

        await category.save()
        category2 = await Category.objects.get()
        assert category2.model_dump() == {
            "id": 3,
            "items": [],
            "name": "Test 2",
            "visibility": True,
        }
        # NOTE how after loading from db all fields are set explicitly
        # as this is what happens when you populate a model from db
        assert category2.model_dump(exclude_unset=True) == {
            "id": 3,
            "items": [],
            "name": "Test 2",
            "visibility": True,
        }
