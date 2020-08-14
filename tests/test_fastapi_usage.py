import databases
import sqlalchemy
from fastapi import FastAPI
from fastapi.testclient import TestClient

import ormar
from tests.settings import DATABASE_URL

app = FastAPI()

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


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


@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    return item


client = TestClient(app)


def test_read_main():
    response = client.post(
        "/items/", json={"name": "test", "id": 1, "category": {"name": "test cat"}}
    )
    assert response.status_code == 200
    assert response.json() == {
        "category": {"id": None, "name": "test cat"},
        "id": 1,
        "name": "test",
    }
    item = Item(**response.json())
    assert item.id == 1
