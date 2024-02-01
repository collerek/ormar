from typing import Optional
from uuid import UUID, uuid4

import ormar
import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient

from tests.settings import create_config
from tests.lifespan import lifespan, init_tests


base_ormar_config = create_config()
app = FastAPI(lifespan=lifespan(base_ormar_config))


class CA(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="cas")

    id: UUID = ormar.UUID(primary_key=True, default=uuid4)
    ca_name: str = ormar.Text(default="")


class CB1(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="cb1s")

    id: UUID = ormar.UUID(primary_key=True, default=uuid4)
    cb1_name: str = ormar.Text(default="")
    ca1: Optional[CA] = ormar.ForeignKey(CA, nullable=True)


class CB2(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="cb2s")

    id: UUID = ormar.UUID(primary_key=True, default=uuid4)
    cb2_name: str = ormar.Text(default="")
    ca2: Optional[CA] = ormar.ForeignKey(CA, nullable=True)


create_test_database = init_tests(base_ormar_config)


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
        raw_names_w_o_modules = [x.split("__")[-1] for x in components.keys()]
        assert all(x in raw_names_w_o_modules for x in ["CA", "CB1", "CB2"])
        pk_onlys = [x for x in list(raw_names_w_o_modules) if x.startswith("PkOnly")]
        assert len(pk_onlys) == 4
