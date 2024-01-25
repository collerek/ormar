import databases
import ormar
import pytest
import sqlalchemy
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient
from ormar import Extra

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


class Item(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
        extra=Extra.ignore,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@app.post("/item/", response_model=Item)
async def create_item(item: Item):
    return await item.save()


@pytest.mark.asyncio
async def test_extra_parameters_in_request():
    client = AsyncClient(app=app, base_url="http://testserver")
    async with client as client, LifespanManager(app):
        data = {"name": "Name", "extraname": "to ignore"}
        resp = await client.post("item/", json=data)
        assert resp.status_code == 200
        assert "name" in resp.json()
        assert resp.json().get("name") == "Name"
