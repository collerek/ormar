import pytest
import sqlalchemy
from fastapi import FastAPI
from starlette.testclient import TestClient

from tests.settings import DATABASE_URL
from tests.test_inheritance_and_pydantic_generation.test_geting_the_pydantic_models import (
    Category,
    Item,
    MutualA,
    MutualB,
    SelfRef,
    database,
    metadata,
)  # type: ignore

app = FastAPI()
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


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


async def create_category(category: Category):
    return await Category(**category.dict()).save()


create_category.__annotations__["category"] = Category.get_pydantic(exclude={"id"})
app.post("/categories/", response_model=Category)(create_category)


@app.post(
    "/selfrefs/",
    response_model=SelfRef.get_pydantic(exclude={"parent", "children__name"}),
)
async def create_selfref(
    selfref: SelfRef.get_pydantic(exclude={"children__name"}),  # type: ignore
):
    selfr = SelfRef(**selfref.dict())
    await selfr.save()
    if selfr.children:
        for child in selfr.children:
            await child.upsert()
    return selfr


@app.get("/selfrefs/{ref_id}/")
async def get_selfref(ref_id: int):
    selfr = await SelfRef.objects.select_related("children").get(id=ref_id)
    return selfr


def test_read_main():
    client = TestClient(app)
    with client as client:
        test_category = dict(name="Foo", id=12)
        response = client.post("/categories/", json=test_category)
        assert response.status_code == 200
        cat = Category(**response.json())
        assert cat.name == "Foo"
        assert cat.id == 1
        assert cat.items == []

        test_selfref = dict(id=1, name="test")
        test_selfref2 = dict(id=2, name="test2", parent={"id": 1})
        test_selfref3 = dict(id=3, name="test3", children=[{"id": 4, "name": "aaa"}])

        response = client.post("/selfrefs/", json=test_selfref)
        assert response.status_code == 200
        self_ref = SelfRef(**response.json())
        assert self_ref.id == 1
        assert self_ref.name == "test"
        assert self_ref.parent is None
        assert self_ref.children == []

        response = client.post("/selfrefs/", json=test_selfref2)
        assert response.status_code == 200
        self_ref = SelfRef(**response.json())
        assert self_ref.id == 2
        assert self_ref.name == "test2"
        assert self_ref.parent is None
        assert self_ref.children == []

        response = client.post("/selfrefs/", json=test_selfref3)
        assert response.status_code == 200
        self_ref = SelfRef(**response.json())
        assert self_ref.id == 3
        assert self_ref.name == "test3"
        assert self_ref.parent is None
        assert self_ref.children[0].dict() == {"id": 4}

        response = client.get("/selfrefs/3/")
        assert response.status_code == 200
        check_children = SelfRef(**response.json())
        assert check_children.children[0].dict() == {
            "children": [],
            "id": 4,
            "name": "selfref",
            "parent": {"id": 3, "name": "test3"},
        }

        response = client.get("/selfrefs/2/")
        assert response.status_code == 200
        check_children = SelfRef(**response.json())
        assert check_children.dict() == {
            "children": [],
            "id": 2,
            "name": "test2",
            "parent": {"id": 1},
        }
