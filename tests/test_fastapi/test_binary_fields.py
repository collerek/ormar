import base64
import json
import uuid
from enum import Enum
from typing import List

import databases
import pytest
import sqlalchemy
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient

import ormar
from tests.settings import DATABASE_URL

app = FastAPI()

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()
app.state.database = database

headers = {"content-type": "application/json"}


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


blob3 = b"\xc3\x28"
blob4 = b"\xf0\x28\x8c\x28"
blob5 = b"\xee"
blob6 = b"\xff"


base_ormar_config = ormar.OrmarConfig(
    metadata=metadata,
    database=database,
)


class BinaryEnum(Enum):
    blob3 = blob3
    blob4 = blob4
    blob5 = blob5
    blob6 = blob6


class BinaryThing(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename = "things")

    id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4)
    name: str = ormar.Text(default="")
    bt: str = ormar.Enum(enum_class=BinaryEnum, represent_as_base64_str=True,
    )


@app.get("/things", response_model=List[BinaryThing])
async def read_things():
    return await BinaryThing.objects.order_by("name").all()


@app.post("/things", response_model=BinaryThing)
async def create_things(thing: BinaryThing):
    thing = await thing.save()
    return thing


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
        response = await client.post(
            "/things",
            json={"bt": base64.b64encode(blob3).decode()},
            headers=headers,
        )
        assert response.status_code == 200
        response = await client.get("/things")
        assert response.json()[0]["bt"] == base64.b64encode(blob3).decode()
        thing = BinaryThing(**response.json()[0])
        assert thing.__dict__["bt"] == blob3


def test_schema():
    schema = BinaryThing.schema()
    assert schema["properties"]["bt"]["format"] == "base64"
    converted_choices = ["7g==", "/w==", "8CiMKA==", "wyg="]
    assert len(schema["properties"]["bt"]["enum"]) == 4
    assert all(
        choice in schema["properties"]["bt"]["enum"] for choice in converted_choices
    )
    assert schema["example"]["bt"] == "string"
