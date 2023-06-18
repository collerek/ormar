from typing import Optional
from uuid import UUID, uuid4

import databases
import pytest
import sqlalchemy
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient

import ormar

app = FastAPI()
DATABASE_URL = "sqlite:///db.sqlite"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class CA(ormar.Model):
    class Meta(BaseMeta):
        tablename = "cas"

    id: UUID = ormar.UUID(primary_key=True, default=uuid4)
    ca_name: str = ormar.Text(default="")


class CB1(ormar.Model):
    class Meta(BaseMeta):
        tablename = "cb1s"

    id: UUID = ormar.UUID(primary_key=True, default=uuid4)
    cb1_name: str = ormar.Text(default="")
    ca1: Optional[CA] = ormar.ForeignKey(CA, nullable=True)


class CB2(ormar.Model):
    class Meta(BaseMeta):
        tablename = "cb2s"

    id: UUID = ormar.UUID(primary_key=True, default=uuid4)
    cb2_name: str = ormar.Text(default="")
    ca2: Optional[CA] = ormar.ForeignKey(CA, nullable=True)


@app.get("/ca", response_model=CA)
async def get_ca():  # pragma: no cover
    return None


@app.get("/cb1", response_model=CB1)
async def get_cb1():  # pragma: no cover
    return None


@app.get("/cb2", response_model=CB2)
async def get_cb2():  # pragma: no cover
    return None


@pytest.mark.asyncio
async def test_all_endpoints():
    client = AsyncClient(app=app, base_url="http://testserver")
    async with client as client, LifespanManager(app):
        response = await client.get("/openapi.json")
        assert response.status_code == 200, response.text
        schema = response.json()
        components = schema["components"]["schemas"]
        assert all(x in components for x in ["CA", "CB1", "CB2"])
        pk_onlys = [x for x in list(components.keys()) if x.startswith("PkOnly")]
        assert len(pk_onlys) == 2
