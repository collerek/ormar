from typing import List

import databases
import ormar
import pytest
import sqlalchemy

from tests.settings import DATABASE_URL

metadata = sqlalchemy.MetaData()
database = databases.Database(DATABASE_URL, force_rollback=True)


class Category(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename="categories",
        metadata=metadata,
        database=database,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, default="Test", nullable=True)
    visibility: bool = ormar.Boolean(default=True)


class Item(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename="items",
        metadata=metadata,
        database=database,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    price: float = ormar.Float(default=9.99)
    categories: List[Category] = ormar.ManyToMany(Category)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_exclude_default():
    async with database:
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
        assert category2.dict(exclude_defaults=True) == {"id": 1, "items": []}
        assert category2.json(exclude_defaults=True) == '{"id":1,"items":[]}'


@pytest.mark.asyncio
async def test_exclude_none():
    async with database:
        category = Category(id=2, name=None)
        assert category.dict() == {
            "id": 2,
            "items": [],
            "name": None,
            "visibility": True,
        }
        assert category.dict(exclude_none=True) == {
            "id": 2,
            "items": [],
            "visibility": True,
        }

        await category.save()
        category2 = await Category.objects.get()
        assert category2.dict() == {
            "id": 2,
            "items": [],
            "name": None,
            "visibility": True,
        }
        assert category2.dict(exclude_none=True) == {
            "id": 2,
            "items": [],
            "visibility": True,
        }
        assert (
            category2.json(exclude_none=True) == '{"id":2,"visibility":true,"items":[]}'
        )


@pytest.mark.asyncio
async def test_exclude_unset():
    async with database:
        category = Category(id=3, name="Test 2")
        assert category.dict() == {
            "id": 3,
            "items": [],
            "name": "Test 2",
            "visibility": True,
        }
        assert category.dict(exclude_unset=True) == {
            "id": 3,
            "items": [],
            "name": "Test 2",
        }

        await category.save()
        category2 = await Category.objects.get()
        assert category2.dict() == {
            "id": 3,
            "items": [],
            "name": "Test 2",
            "visibility": True,
        }
        # NOTE how after loading from db all fields are set explicitly
        # as this is what happens when you populate a model from db
        assert category2.dict(exclude_unset=True) == {
            "id": 3,
            "items": [],
            "name": "Test 2",
            "visibility": True,
        }
