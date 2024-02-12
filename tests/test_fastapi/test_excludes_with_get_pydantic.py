from typing import ForwardRef, Optional

import ormar
import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient

from tests.lifespan import init_tests, lifespan
from tests.settings import create_config

base_ormar_config = create_config()
app = FastAPI(lifespan=lifespan(base_ormar_config))


class SelfRef(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="self_refs")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, default="selfref")
    parent = ormar.ForeignKey(ForwardRef("SelfRef"), related_name="children")


SelfRef.update_forward_refs()


class Category(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="categories")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Item(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, default="test")
    category: Optional[Category] = ormar.ForeignKey(Category, nullable=True)


create_test_database = init_tests(base_ormar_config)


async def create_category(category: Category):
    return await Category(**category.model_dump()).save()


create_category.__annotations__["category"] = Category.get_pydantic(exclude={"id"})
app.post("/categories/", response_model=Category)(create_category)


@app.post(
    "/selfrefs/",
    response_model=SelfRef.get_pydantic(exclude={"parent", "children__name"}),
)
async def create_selfref(
    selfref: SelfRef.get_pydantic(  # type: ignore
        exclude={"children__name"}  # noqa: F821
    ),
):
    selfr = SelfRef(**selfref.model_dump())
    await selfr.save()
    if selfr.children:
        for child in selfr.children:
            await child.upsert()
    return selfr


@app.get("/selfrefs/{ref_id}/")
async def get_selfref(ref_id: int):
    selfr = await SelfRef.objects.select_related("children").get(id=ref_id)
    return selfr


@pytest.mark.asyncio
async def test_read_main():
    client = AsyncClient(app=app, base_url="http://testserver")
    async with client as client, LifespanManager(app):
        test_category = dict(name="Foo", id=12)
        response = await client.post("/categories/", json=test_category)
        assert response.status_code == 200
        cat = Category(**response.json())
        assert cat.name == "Foo"
        assert cat.id == 1
        assert cat.items == []

        test_selfref = dict(name="test")
        test_selfref2 = dict(name="test2", parent={"id": 1})
        test_selfref3 = dict(name="test3", children=[{"name": "aaa"}])

        response = await client.post("/selfrefs/", json=test_selfref)
        assert response.status_code == 200
        self_ref = SelfRef(**response.json())
        assert self_ref.id == 1
        assert self_ref.name == "test"
        assert self_ref.parent is None
        assert self_ref.children == []

        response = await client.post("/selfrefs/", json=test_selfref2)
        assert response.status_code == 200
        self_ref = SelfRef(**response.json())
        assert self_ref.id == 2
        assert self_ref.name == "test2"
        assert self_ref.parent is None
        assert self_ref.children == []

        response = await client.post("/selfrefs/", json=test_selfref3)
        assert response.status_code == 200
        self_ref = SelfRef(**response.json())
        assert self_ref.id == 3
        assert self_ref.name == "test3"
        assert self_ref.parent is None
        assert self_ref.children[0].model_dump() == {"id": 4}

        response = await client.get("/selfrefs/3/")
        assert response.status_code == 200
        check_children = SelfRef(**response.json())
        assert check_children.children[0].model_dump() == {
            "children": [],
            "id": 4,
            "name": "selfref",
            "parent": {"id": 3, "name": "test3"},
        }

        response = await client.get("/selfrefs/2/")
        assert response.status_code == 200
        check_children = SelfRef(**response.json())
        assert check_children.model_dump() == {
            "children": [],
            "id": 2,
            "name": "test2",
            "parent": {"id": 1},
        }

        response = await client.get("/selfrefs/1/")
        assert response.status_code == 200
        check_children = SelfRef(**response.json())
        assert check_children.model_dump() == {
            "children": [{"id": 2, "name": "test2"}],
            "id": 1,
            "name": "test",
            "parent": None,
        }
