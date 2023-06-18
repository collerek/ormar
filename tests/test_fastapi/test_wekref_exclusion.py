from typing import List, Optional
from uuid import UUID, uuid4

import databases
import pydantic
import pytest
import sqlalchemy
from fastapi import FastAPI
from httpx import AsyncClient

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


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


class BaseMeta(ormar.ModelMeta):
    database = database
    metadata = metadata


class OtherThing(ormar.Model):
    class Meta(BaseMeta):
        tablename = "other_things"

    id: UUID = ormar.UUID(primary_key=True, default=uuid4)
    name: str = ormar.Text(default="")
    ot_contents: str = ormar.Text(default="")


class Thing(ormar.Model):
    class Meta(BaseMeta):
        tablename = "things"

    id: UUID = ormar.UUID(primary_key=True, default=uuid4)
    name: str = ormar.Text(default="")
    js: pydantic.Json = ormar.JSON(nullable=True)
    other_thing: Optional[OtherThing] = ormar.ForeignKey(OtherThing, nullable=True)


@app.post("/test/1")
async def post_test_1():
    # don't split initialization and attribute assignment
    ot = await OtherThing(ot_contents="otc").save()
    await Thing(other_thing=ot, name="t1").save()
    await Thing(other_thing=ot, name="t2").save()
    await Thing(other_thing=ot, name="t3").save()

    # if you do not care about returned object you can even go with bulk_create
    # all of them are created in one transaction
    # things = [Thing(other_thing=ot, name='t1'),
    #           Thing(other_thing=ot, name="t2"),
    #           Thing(other_thing=ot, name="t3")]
    # await Thing.objects.bulk_create(things)


@app.get("/test/2", response_model=List[Thing])
async def get_test_2():
    # if you only query for one use get or first
    ot = await OtherThing.objects.get()
    ts = await ot.things.all()
    # specifically null out the relation on things before return
    for t in ts:
        t.remove(ot, name="other_thing")
    return ts


@app.get("/test/3", response_model=List[Thing])
async def get_test_3():
    ot = await OtherThing.objects.select_related("things").get()
    # exclude unwanted field while ot is still in scope
    # in order not to pass it to fastapi
    return [t.dict(exclude={"other_thing"}) for t in ot.things]


@app.get("/test/4", response_model=List[Thing], response_model_exclude={"other_thing"})
async def get_test_4():
    ot = await OtherThing.objects.get()
    # query from the active side
    return await Thing.objects.all(other_thing=ot)


@app.get("/get_ot/", response_model=OtherThing)
async def get_ot():
    return await OtherThing.objects.get()


# more real life (usually) is not getting some random OT and get it's Things
# but query for a specific one by some kind of id
@app.get(
    "/test/5/{thing_id}",
    response_model=List[Thing],
    response_model_exclude={"other_thing"},
)
async def get_test_5(thing_id: UUID):
    return await Thing.objects.all(other_thing__id=thing_id)


@app.get(
    "/test/error", response_model=List[Thing], response_model_exclude={"other_thing"}
)
async def get_weakref():
    ots = await OtherThing.objects.all()
    ot = ots[0]
    ts = await ot.things.all()
    return ts


@pytest.mark.asyncio
async def test_endpoints():
    client = AsyncClient(app=app, base_url="http://testserver")
    async with client:
        resp = await client.post("/test/1")
        assert resp.status_code == 200

        resp2 = await client.get("/test/2")
        assert resp2.status_code == 200
        assert len(resp2.json()) == 3

        resp3 = await client.get("/test/3")
        assert resp3.status_code == 200
        assert len(resp3.json()) == 3

        resp4 = await client.get("/test/4")
        assert resp4.status_code == 200
        assert len(resp4.json()) == 3

        ot = OtherThing(**(await client.get("/get_ot/")).json())
        resp5 = await client.get(f"/test/5/{ot.id}")
        assert resp5.status_code == 200
        assert len(resp5.json()) == 3

        resp6 = await client.get("/test/error")
        assert resp6.status_code == 200
        assert len(resp6.json()) == 3
