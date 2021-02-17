from typing import Optional
from uuid import UUID, uuid4

import databases
import sqlalchemy
from fastapi import FastAPI
from starlette.testclient import TestClient

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
async def get_ca():
    return None


@app.get("/cb1", response_model=CB1)
async def get_cb1():
    return None


@app.get("/cb2", response_model=CB2)
async def get_cb2():
    return None


def test_all_endpoints():
    client = TestClient(app)
    with client as client:
        response = client.get("/openapi.json")
        assert response.status_code == 200, response.text
        schema = response.json()
        components = schema["components"]["schemas"]
        assert all(x in components for x in ["CA", "CB1", "CB2"])
        pk_onlys = [x for x in list(components.keys()) if x.startswith("PkOnly")]
        assert len(pk_onlys) == 2
