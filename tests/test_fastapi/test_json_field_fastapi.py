# type: ignore
import uuid
from typing import List

import ormar
import pydantic
import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient

from tests.lifespan import lifespan, init_tests
from tests.settings import create_config


base_ormar_config = create_config()
app = FastAPI(lifespan=lifespan(base_ormar_config))


class Thing(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="things")

    id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4)
    name: str = ormar.Text(default="")
    js: pydantic.Json = ormar.JSON()


create_test_database = init_tests(base_ormar_config)


@app.get("/things", response_model=List[Thing])
async def read_things():
    return await Thing.objects.order_by("name").all()


@app.get("/things_with_sample", response_model=List[Thing])
async def read_things_sample():
    await Thing(name="b", js=["asdf", "asdf", "bobby", "nigel"]).save()
    await Thing(name="a", js='["lemon", "raspberry", "lime", "pumice"]').save()
    return await Thing.objects.order_by("name").all()


@app.get("/things_with_sample_after_init", response_model=Thing)
async def read_things_init():
    thing1 = Thing(js="{}")
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


@app.get("/things_untyped")
async def read_things_untyped():
    return await Thing.objects.order_by("name").all()


@pytest.mark.asyncio
async def test_json_is_required_if_not_nullable():
    with pytest.raises(pydantic.ValidationError):
        Thing()


@pytest.mark.asyncio
async def test_json_is_not_required_if_nullable():
    class Thing2(ormar.Model):
        ormar_config = base_ormar_config.copy(tablename="things2")

        id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4)
        name: str = ormar.Text(default="")
        js: pydantic.Json = ormar.JSON(nullable=True)

    Thing2()


@pytest.mark.asyncio
async def test_setting_values_after_init():
    async with base_ormar_config.database:
        t1 = Thing(id="67a82813-d90c-45ff-b546-b4e38d7030d7", name="t1", js=["thing1"])
        assert '["thing1"]' in t1.model_dump_json()
        await t1.save()
        t1.model_dump_json()
        assert '["thing1"]' in t1.model_dump_json()

        assert '["thing1"]' in (await Thing.objects.get(id=t1.id)).model_dump_json()
        await t1.update()
        assert '["thing1"]' in (await Thing.objects.get(id=t1.id)).model_dump_json()


@pytest.mark.asyncio
async def test_read_main():
    client = AsyncClient(app=app, base_url="http://testserver")
    async with client as client, LifespanManager(app):
        response = await client.get("/things_with_sample")
        assert response.status_code == 200

        # check if raw response not double encoded
        assert '["lemon","raspberry","lime","pumice"]' in response.text

        # parse json and check that we get lists not strings
        resp = response.json()
        assert resp[0].get("js") == ["lemon", "raspberry", "lime", "pumice"]
        assert resp[1].get("js") == ["asdf", "asdf", "bobby", "nigel"]

        # create a new one
        response = await client.post(
            "/things", json={"js": ["test", "test2"], "name": "c"}
        )
        assert response.json().get("js") == ["test", "test2"]

        # get all with new one
        response = await client.get("/things")
        assert response.status_code == 200
        assert '["test","test2"]' in response.text
        resp = response.json()
        assert resp[0].get("js") == ["lemon", "raspberry", "lime", "pumice"]
        assert resp[1].get("js") == ["asdf", "asdf", "bobby", "nigel"]
        assert resp[2].get("js") == ["test", "test2"]

        response = await client.get("/things_with_sample_after_init")
        assert response.status_code == 200
        resp = response.json()
        assert resp.get("js") == ["js", "set", "after", "constructor"]

        # test new with after constructor
        response = await client.get("/things")
        resp = response.json()
        assert resp[0].get("js") == ["lemon", "raspberry", "lime", "pumice"]
        assert resp[1].get("js") == ["asdf", "asdf", "bobby", "nigel"]
        assert resp[2].get("js") == ["test", "test2"]
        assert resp[3].get("js") == ["js", "set", "after", "constructor"]

        response = await client.put("/update_thing", json=resp[3])
        assert response.status_code == 200
        resp = response.json()
        assert resp.get("js") == ["js", "set", "after", "update"]

        # test new with after constructor
        response = await client.get("/things_untyped")
        resp = response.json()
        assert resp[0].get("js") == ["lemon", "raspberry", "lime", "pumice"]
        assert resp[1].get("js") == ["asdf", "asdf", "bobby", "nigel"]
        assert resp[2].get("js") == ["test", "test2"]
        assert resp[3].get("js") == ["js", "set", "after", "update"]
