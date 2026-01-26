import base64
import uuid
from enum import Enum
from typing import List

import ormar
import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from tests.lifespan import init_tests, lifespan
from tests.settings import create_config

headers = {"content-type": "application/json"}
base_ormar_config = create_config()
app = FastAPI(lifespan=lifespan(base_ormar_config))


blob3 = b"\xc3\x83\x28"
blob4 = b"\xf0\x28\x8c\x28"
blob5 = b"\xee"
blob6 = b"\xff"


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


create_test_database = init_tests(base_ormar_config)


@app.get("/things", response_model=List[BinaryThing])
async def read_things():
    return await BinaryThing.objects.order_by("name").all()


@app.post("/things", response_model=BinaryThing)
async def create_things(thing: BinaryThing):
    thing = await thing.save()
    return thing


@pytest.mark.asyncio
async def test_read_main():
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
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
        assert thing.bt == base64.b64encode(blob3).decode()


def test_schema():
    schema = BinaryThing.model_json_schema()
    assert schema["properties"]["bt"]["format"] == "base64"
    assert schema["example"]["bt"] == "string"
