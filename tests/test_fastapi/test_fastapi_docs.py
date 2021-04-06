from typing import List

import databases
import pytest
import sqlalchemy
from fastapi import FastAPI
from starlette.testclient import TestClient

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


class LocalMeta:
    metadata = metadata
    database = database


class Category(ormar.Model):
    class Meta(LocalMeta):
        tablename = "categories"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Item(ormar.Model):
    class Meta(LocalMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    categories = ormar.ManyToMany(Category)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@app.get("/items/", response_model=List[Item])
async def get_items():
    items = await Item.objects.select_related("categories").all()
    return items


@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    await item.save()
    return item


@app.post("/items/add_category/", response_model=Item)
async def add_item_category(item: Item, category: Category):
    await item.categories.add(category)
    return item


@app.post("/categories/", response_model=Category)
async def create_category(category: Category):
    await category.save()
    return category


def test_all_endpoints():
    client = TestClient(app)
    with client as client:
        response = client.post("/categories/", json={"name": "test cat"})
        category = response.json()
        response = client.post("/categories/", json={"name": "test cat2"})
        category2 = response.json()

        response = client.post("/items/", json={"name": "test", "id": 1})
        item = Item(**response.json())
        assert item.pk is not None

        response = client.post(
            "/items/add_category/", json={"item": item.dict(), "category": category}
        )
        item = Item(**response.json())
        assert len(item.categories) == 1
        assert item.categories[0].name == "test cat"

        client.post(
            "/items/add_category/", json={"item": item.dict(), "category": category2}
        )

        response = client.get("/items/")
        items = [Item(**item) for item in response.json()]
        assert items[0] == item
        assert len(items[0].categories) == 2
        assert items[0].categories[0].name == "test cat"
        assert items[0].categories[1].name == "test cat2"

        response = client.get("/docs/")
        assert response.status_code == 200
        assert b"<title>FastAPI - Swagger UI</title>" in response.content


def test_schema_modification():
    schema = Item.schema()
    assert any(
        x.get("type") == "array" for x in schema["properties"]["categories"]["anyOf"]
    )
    assert schema["properties"]["categories"]["title"] == "Categories"


def test_schema_gen():
    schema = app.openapi()
    assert "Category" in schema["components"]["schemas"]
    assert "Item" in schema["components"]["schemas"]
