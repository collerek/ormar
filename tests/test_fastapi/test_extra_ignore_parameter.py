import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

import ormar
from ormar import Extra
from tests.lifespan import init_tests, lifespan
from tests.settings import create_config

base_ormar_config = create_config()
app = FastAPI(lifespan=lifespan(base_ormar_config))


class Item(ormar.Model):
    ormar_config = base_ormar_config.copy(extra=Extra.ignore)

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


create_test_database = init_tests(base_ormar_config)


@app.post("/item/", response_model=Item)
async def create_item(item: Item):
    return await item.save()


@pytest.mark.asyncio
async def test_extra_parameters_in_request():
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    async with client as client, LifespanManager(app):
        data = {"name": "Name", "extraname": "to ignore"}
        resp = await client.post("item/", json=data)
        assert resp.status_code == 200
        assert "name" in resp.json()
        assert resp.json().get("name") == "Name"
