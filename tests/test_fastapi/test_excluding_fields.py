from typing import List

import databases
import pytest
import sqlalchemy
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient

import ormar
from tests.settings import DATABASE_URL

app = FastAPI()
metadata = sqlalchemy.MetaData()
database = databases.Database(DATABASE_URL, force_rollback=True)
app.state.database = database


@app.on_event("startup")
async def startup() -> None:
    database_ = app.state.database
    if not database_.is_connected:
        await database_.connect()


@app.on_event("shutdown")
async def shutdown() -> None:
    database_ = app.state.database
    if database_.is_connected:
        await database_.disconnect()


class Category(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename = "categories",
        metadata = metadata,
        database = database,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Item(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename = "items",
        metadata = metadata,
        database = database,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    categories: List[Category] = ormar.ManyToMany(Category)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    await item.save_related(follow=True, save_all=True)
    return item


@app.get("/items/{item_id}")
async def get_item(item_id: int):
    item = await Item.objects.select_related("categories").get(pk=item_id)
    return item.dict(exclude_primary_keys=True, exclude_through_models=True)


@app.get("/categories/{category_id}")
async def get_category(category_id: int):
    category = await Category.objects.select_related("items").get(pk=category_id)
    return category.dict(exclude_primary_keys=True)


@app.get("/categories/nt/{category_id}")
async def get_category_no_through(category_id: int):
    category = await Category.objects.select_related("items").get(pk=category_id)
    result = category.dict(exclude_through_models=True)
    return result


@app.get("/categories/ntp/{category_id}")
async def get_category_no_pk_through(category_id: int):
    category = await Category.objects.select_related("items").get(pk=category_id)
    return category.dict(exclude_through_models=True, exclude_primary_keys=True)


@app.get(
    "/items/fex/{item_id}",
    response_model=Item,
    response_model_exclude={
        "id",
        "categories__id",
        "categories__itemcategory",
        "categories__items",
    },
)
async def get_item_excl(item_id: int):
    item = await Item.objects.select_all().get(pk=item_id)
    return item


@pytest.mark.asyncio
async def test_all_endpoints():
    client = AsyncClient(app=app, base_url="http://testserver")
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

        no_pk_item2 = (await client.get(f"/items/fex/{item_check.id}")).json()
        assert no_pk_item2 == item
