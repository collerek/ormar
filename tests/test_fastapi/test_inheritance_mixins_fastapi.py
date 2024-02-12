import datetime

import pytest
import ormar
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient
from typing import Optional

from tests.lifespan import lifespan, init_tests
from tests.settings import create_config


base_ormar_config = create_config()
app = FastAPI(lifespan=lifespan(base_ormar_config))


class AuditMixin:
    created_by: str = ormar.String(max_length=100)
    updated_by: str = ormar.String(max_length=100, default="Sam")


class DateFieldsMixins:
    created_date: datetime.datetime = ormar.DateTime(default=datetime.datetime.now)
    updated_date: datetime.datetime = ormar.DateTime(default=datetime.datetime.now)


class Category(ormar.Model, DateFieldsMixins, AuditMixin):
    ormar_config = base_ormar_config.copy(tablename="categories")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50, unique=True, index=True)
    code: int = ormar.Integer()


class Subject(ormar.Model, DateFieldsMixins):
    ormar_config = base_ormar_config.copy(tablename="subjects")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50, unique=True, index=True)
    category: Optional[Category] = ormar.ForeignKey(Category)


create_test_database = init_tests(base_ormar_config)



@app.post("/subjects/", response_model=Subject)
async def create_item(item: Subject):
    return item


@app.post("/categories/", response_model=Category)
async def create_category(category: Category):
    await category.save()
    return category


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

        cat_dict = cat.model_dump()
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
