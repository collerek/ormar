import datetime
from typing import List, Optional, Union

import ormar
import pydantic
import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient
from pydantic import Field

from tests.lifespan import lifespan, init_tests
from tests.settings import create_config


base_ormar_config = create_config()
app = FastAPI(lifespan=lifespan(base_ormar_config))


class PTestA(pydantic.BaseModel):
    c: str
    d: bytes
    e: datetime.datetime


class PTestP(pydantic.BaseModel):
    a: int
    b: Optional[PTestA]


class Category(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="categories")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Item(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    pydantic_int: Optional[int] = None
    test_P: List[PTestP] = Field(default_factory=list)
    test_P_or_A: Union[int, str, None] = None
    categories = ormar.ManyToMany(Category)


create_test_database = init_tests(base_ormar_config)



@app.get("/items/", response_model=List[Item])
async def get_items():
    items = await Item.objects.select_related("categories").all()
    for item in items:
        item.test_P_or_A = 2
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


@pytest.mark.asyncio
async def test_all_endpoints():
    client = AsyncClient(app=app, base_url="http://testserver")
    async with client as client, LifespanManager(app):
        response = await client.post("/categories/", json={"name": "test cat"})
        assert response.status_code == 200
        category = response.json()
        response = await client.post("/categories/", json={"name": "test cat2"})
        assert response.status_code == 200
        category2 = response.json()

        response = await client.post(
            "/items/", json={"name": "test", "id": 1, "test_P_or_A": 0}
        )
        assert response.status_code == 200
        item = Item(**response.json())
        assert item.pk is not None

        response = await client.post(
            "/items/add_category/",
            json={"item": item.model_dump(), "category": category},
        )
        assert response.status_code == 200
        item = Item(**response.json())
        assert len(item.categories) == 1
        assert item.categories[0].name == "test cat"

        await client.post(
            "/items/add_category/",
            json={"item": item.model_dump(), "category": category2},
        )

        response = await client.get("/items/")
        assert response.status_code == 200
        items = [Item(**item) for item in response.json()]
        assert items[0] == item
        assert len(items[0].categories) == 2
        assert items[0].categories[0].name == "test cat"
        assert items[0].categories[1].name == "test cat2"

        response = await client.get("/docs")
        assert response.status_code == 200
        assert b"<title>FastAPI - Swagger UI</title>" in response.content


def test_schema_modification():
    schema = Item.model_json_schema()
    assert any(
        x.get("type") == "array" for x in schema["properties"]["categories"]["anyOf"]
    )
    assert schema["properties"]["categories"]["title"] == "Categories"
    assert schema["example"] == {
        "categories": [{"id": 0, "name": "string"}],
        "id": 0,
        "name": "string",
        "pydantic_int": 0,
        "test_P": [{"a": 0, "b": {"c": "string", "d": "string", "e": "string"}}],
        "test_P_or_A": (0, "string"),
    }

    schema = Category.model_json_schema()
    assert schema["$defs"]["Category"]["example"] == {
        "id": 0,
        "name": "string",
        "items": [
            {
                "id": 0,
                "name": "string",
                "pydantic_int": 0,
                "test_P": [
                    {"a": 0, "b": {"c": "string", "d": "string", "e": "string"}}
                ],
                "test_P_or_A": (0, "string"),
            }
        ],
    }


def test_schema_gen():
    schema = app.openapi()
    assert "Category" in schema["components"]["schemas"]
    subschemas = [x.split("__")[-1] for x in schema["components"]["schemas"]]
    assert "Item-Input" in subschemas
    assert "Item-Output" in subschemas
