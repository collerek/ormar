from typing import Optional

import databases
import ormar
import pytest
import sqlalchemy
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient

from tests.settings import DATABASE_URL

app = FastAPI()

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Category(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename="categories",
        metadata=metadata,
        database=database,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Item(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename="items",
        metadata=metadata,
        database=database,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    category: Optional[Category] = ormar.ForeignKey(Category, nullable=True)


@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    return item


@pytest.mark.asyncio
async def test_read_main():
    client = AsyncClient(app=app, base_url="http://testserver")
    async with client as client, LifespanManager(app):
        response = await client.post(
            "/items/", json={"name": "test", "id": 1, "category": {"name": "test cat"}}
        )
        assert response.status_code == 200
        assert response.json() == {
            "category": {
                "id": None,
                "name": "test cat",
            },
            "id": 1,
            "name": "test",
        }
        item = Item(**response.json())
        assert item.id == 1
        assert item.category.items[0].id == 1
