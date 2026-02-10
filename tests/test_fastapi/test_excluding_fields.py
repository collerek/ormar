from typing import List

import ormar
import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from tests.lifespan import init_tests, lifespan
from tests.settings import create_config

base_ormar_config = create_config()
app = FastAPI(lifespan=lifespan(base_ormar_config))


class Category(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="categories")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Item(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="items")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    categories: List[Category] = ormar.ManyToMany(Category)


create_test_database = init_tests(base_ormar_config)


@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    await item.save_related(follow=True, save_all=True)
    return item


@app.get("/items/{item_id}")
async def get_item(item_id: int):
    item = await Item.objects.select_related("categories").get(pk=item_id)
    return item.model_dump(exclude_primary_keys=True, exclude_through_models=True)


@app.get("/categories/{category_id}")
async def get_category(category_id: int):
    category = await Category.objects.select_related("items").get(pk=category_id)
    return category.model_dump(exclude_primary_keys=True)


@app.get("/categories/nt/{category_id}")
async def get_category_no_through(category_id: int):
    category = await Category.objects.select_related("items").get(pk=category_id)
    result = category.model_dump(exclude_through_models=True)
    return result


@app.get("/categories/ntp/{category_id}")
async def get_category_no_pk_through(category_id: int):
    category = await Category.objects.select_related("items").get(pk=category_id)
    return category.model_dump(exclude_through_models=True, exclude_primary_keys=True)


@pytest.mark.asyncio
async def test_all_endpoints():
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    async with client as client, LifespanManager(app):
        item = {
            "name": "test",
            "categories": [{"name": "test cat"}, {"name": "test cat2"}],
        }
        response = await client.post("/items/", json=item)
        item_check = Item(**response.json())
        assert item_check.id is not None
        assert item_check.categories[0].id is not None

        no_pk_item = (await client.get(f"/items/{item_check.id}")).json()
        assert no_pk_item == item

        no_pk_category = (
            await client.get(f"/categories/{item_check.categories[0].id}")
        ).json()
        assert no_pk_category == {
            "items": [
                {
                    "itemcategory": {"category": None, "id": 1, "item": None},
                    "name": "test",
                }
            ],
            "name": "test cat",
        }

        no_through_category = (
            await client.get(f"/categories/nt/{item_check.categories[0].id}")
        ).json()
        assert no_through_category == {
            "id": 1,
            "items": [{"id": 1, "name": "test"}],
            "name": "test cat",
        }

        no_through_category = (
            await client.get(f"/categories/ntp/{item_check.categories[0].id}")
        ).json()
        assert no_through_category == {"items": [{"name": "test"}], "name": "test cat"}
