import datetime

import pytest
import sqlalchemy
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient

from tests.settings import DATABASE_URL
from tests.test_inheritance_and_pydantic_generation.test_inheritance_mixins import (  # noqa: E501
    Category,
    Subject,
    metadata,
)
from tests.test_inheritance_and_pydantic_generation.test_inheritance_mixins import (
    db as database,
)

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


@app.post("/subjects/", response_model=Subject)
async def create_item(item: Subject):
    return item


@app.post("/categories/", response_model=Category)
async def create_category(category: Category):
    await category.save()
    return category


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_read_main():
    client = AsyncClient(app=app, base_url="http://testserver")
    async with client as client, LifespanManager(app):
        test_category = dict(name="Foo", code=123, created_by="Sam", updated_by="Max")
        test_subject = dict(name="Bar")

        response = await client.post("/categories/", json=test_category)
        assert response.status_code == 200
        cat = Category(**response.json())
        assert cat.name == "Foo"
        assert cat.created_by == "Sam"
        assert cat.created_date is not None
        assert cat.id == 1

        cat_dict = cat.dict()
        cat_dict["updated_date"] = cat_dict["updated_date"].strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        cat_dict["created_date"] = cat_dict["created_date"].strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        test_subject["category"] = cat_dict
        response = await client.post("/subjects/", json=test_subject)
        assert response.status_code == 200
        sub = Subject(**response.json())
        assert sub.name == "Bar"
        assert sub.category.pk == cat.pk
        assert isinstance(sub.updated_date, datetime.datetime)
