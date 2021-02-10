import uuid
from typing import List

import databases
import pydantic
import pytest
import sqlalchemy
from fastapi import FastAPI
from starlette.testclient import TestClient

import ormar
from tests.settings import DATABASE_URL

app = FastAPI()

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()
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


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class Thing(ormar.Model):
    class Meta(BaseMeta):
        tablename = "things"

    id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4)
    name: str = ormar.Text(default="")
    js: pydantic.Json = ormar.JSON()


@app.get("/things", response_model=List[Thing])
async def read_things():
    return await Thing.objects.order_by("name").all()


@app.get("/things_with_sample", response_model=List[Thing])
async def read_things_sample():
    await Thing(name="b", js=["asdf", "asdf", "bobby", "nigel"]).save()
    await Thing(name="a", js="[\"lemon\", \"raspberry\", \"lime\", \"pumice\"]").save()
    return await Thing.objects.order_by("name").all()


@app.get("/things_with_sample_after_init", response_model=Thing)
async def read_things_init():
    thing1 = Thing()
    thing1.name = "d"
    thing1.js = ["js", "set", "after", "constructor"]
    await thing1.save()
    return thing1


@app.put("/update_thing", response_model=Thing)
async def update_things(thing: Thing):
    thing.js = ["js", "set", "after", "update"]  # type: ignore
    await thing.update()
    return thing


@app.post("/things", response_model=Thing)
async def create_things(thing: Thing):
    thing = await thing.save()
    return thing


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


def test_read_main():
    client = TestClient(app)
    with client as client:
        response = client.get("/things_with_sample")
        assert response.status_code == 200

        # check if raw response not double encoded
        assert '["lemon","raspberry","lime","pumice"]' in response.text

        # parse json and check that we get lists not strings
        resp = response.json()
        assert resp[0].get("js") == ["lemon", "raspberry", "lime", "pumice"]
        assert resp[1].get("js") == ["asdf", "asdf", "bobby", "nigel"]

        # create a new one
        response = client.post("/things", json={"js": ["test", "test2"], "name": "c"})
        assert response.json().get("js") == ["test", "test2"]

        # get all with new one
        response = client.get("/things")
        assert response.status_code == 200
        assert '["test","test2"]' in response.text
        resp = response.json()
        assert resp[0].get("js") == ["lemon", "raspberry", "lime", "pumice"]
        assert resp[1].get("js") == ["asdf", "asdf", "bobby", "nigel"]
        assert resp[2].get("js") == ["test", "test2"]

        response = client.get("/things_with_sample_after_init")
        assert response.status_code == 200
        resp = response.json()
        assert resp.get("js") == ["js", "set", "after", "constructor"]

        # test new with after constructor
        response = client.get("/things")
        resp = response.json()
        assert resp[0].get("js") == ["lemon", "raspberry", "lime", "pumice"]
        assert resp[1].get("js") == ["asdf", "asdf", "bobby", "nigel"]
        assert resp[2].get("js") == ["test", "test2"]
        assert resp[3].get("js") == ["js", "set", "after", "constructor"]

        response = client.put("/update_thing", json=resp[3])
        assert response.status_code == 200
        resp = response.json()
        assert resp.get("js") == ["js", "set", "after", "update"]

        # test new with after constructor
        response = client.get("/things")
        resp = response.json()
        assert resp[0].get("js") == ["lemon", "raspberry", "lime", "pumice"]
        assert resp[1].get("js") == ["asdf", "asdf", "bobby", "nigel"]
        assert resp[2].get("js") == ["test", "test2"]
        assert resp[3].get("js") == ["js", "set", "after", "update"]
