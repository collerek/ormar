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


class Category(ormar.Model):
    __tablename__ = "categories"
    __metadata__ = metadata
    __database__ = database

    id = ormar.Integer(primary_key=True)
    name = ormar.String(length=100)


class Item(ormar.Model):
    __tablename__ = "items"
    __metadata__ = metadata
    __database__ = database

    id = ormar.Integer(primary_key=True)
    name = ormar.String(length=100)
    category = ormar.ForeignKey(Category, nullable=True)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@app.get("/items/", response_model=List[Item])
async def get_items():
    items = await Item.objects.select_related("category").all()
    return [item.dict() for item in items]


@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    item = await Item.objects.create(**item.dict())
    return item.dict()


@app.post("/categories/", response_model=Category)
async def create_category(category: Category):
    category = await Category.objects.create(**category.dict())
    return category.dict()


@app.put("/items/{item_id}")
async def get_item(item_id: int, item: Item):
    item_db = await Item.objects.get(pk=item_id)
    return {"updated_rows": await item_db.update(**item.dict())}


@app.delete("/items/{item_id}")
async def delete_item(item_id: int, item: Item):
    item_db = await Item.objects.get(pk=item_id)
    return {"deleted_rows": await item_db.delete()}


def test_all_endpoints():
    client = TestClient(app)
    with client as client:
        response = client.post("/categories/", json={"name": "test cat"})
        category = response.json()
        response = client.post(
            "/items/", json={"name": "test", "id": 1, "category": category}
        )
        item = Item(**response.json())
        assert item.pk is not None

        response = client.get("/items/")
        items = [Item(**item) for item in response.json()]
        assert items[0] == item

        item.name = "New name"
        response = client.put(f"/items/{item.pk}", json=item.dict())
        assert response.json().get("updated_rows") == 1

        response = client.get("/items/")
        items = [Item(**item) for item in response.json()]
        assert items[0].name == "New name"

        response = client.delete(f"/items/{item.pk}", json=item.dict())
        assert response.json().get("deleted_rows") == 1
        response = client.get("/items/")
        items = response.json()
        assert len(items) == 0
