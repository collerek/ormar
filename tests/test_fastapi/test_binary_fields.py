import base64
import uuid
from contextlib import asynccontextmanager
from enum import Enum
from typing import AsyncIterator, List

import databases
import ormar
import pytest
import sqlalchemy
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient

from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()

headers = {"content-type": "application/json"}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if not database.is_connected:
        await database.connect()
    yield
    if database.is_connected:
        await database.disconnect()


app = FastAPI(lifespan=lifespan)


blob3 = b"\xc3\x83\x28"
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
    ormar_config = base_ormar_config.copy(tablename="things")

    id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4)
    name: str = ormar.Text(default="")
    bt: str = ormar.LargeBinary(represent_as_base64_str=True, max_length=100)


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
        assert response.json()[0]["bt"] == blob3.decode()
        resp_json = response.json()
        resp_json[0]["bt"] = resp_json[0]["bt"].encode()
        thing = BinaryThing(**resp_json[0])
        assert thing.__dict__["bt"] == blob3
        assert thing.bt == base64.b64encode(blob3).decode()


def test_schema():
    schema = BinaryThing.model_json_schema()
    assert schema["properties"]["bt"]["format"] == "base64"
    assert schema["example"]["bt"] == "string"
