from typing import Optional

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
    category: Optional[Category] = ormar.ForeignKey(Category, nullable=True)


create_test_database = init_tests(base_ormar_config)


@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    return item


@pytest.mark.asyncio
async def test_read_main():
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    async with client as client, LifespanManager(app):
        response = await client.post(
            "/items/", json={"name": "test", "id": 1, "category": {"name": "test cat"}}
        )
        assert response.status_code == 200
        assert response.json() == {
            "category": {
                "id": None,
                "items": [
                    {
                        "category": {"id": None, "name": "test cat"},
                        "id": 1,
                        "name": "test",
                    }
                ],
                "name": "test cat",
            },
            "id": 1,
            "name": "test",
        }
        item = Item(**response.json())
        assert item.id == 1
        assert item.category.items[0].id == 1
