from typing import List, Optional

import databases
import pytest
import sqlalchemy
from fastapi import FastAPI
from pydantic.schema import ForwardRef
from starlette import status
from starlette.testclient import TestClient

import ormar

app = FastAPI()
from tests.settings import DATABASE_URL

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
    database = database
    metadata = metadata


CityRef = ForwardRef("City")
CountryRef = ForwardRef("Country")


# models.py
class Country(ormar.Model):
    class Meta(BaseMeta):
        tablename = "countries"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=128, unique=True)
    iso2: str = ormar.String(max_length=3)
    iso3: str = ormar.String(max_length=4, unique=True)
    population: int = ormar.Integer(maximum=10000000000)
    demonym: str = ormar.String(max_length=128)
    native_name: str = ormar.String(max_length=128)
    capital: Optional[CityRef] = ormar.ForeignKey(  # type: ignore
        CityRef, related_name="capital_city", nullable=True
    )
    borders: List[Optional[CountryRef]] = ormar.ManyToMany(  # type: ignore
        CountryRef, nullable=True, skip_reverse=True
    )


class City(ormar.Model):
    class Meta(BaseMeta):
        tablename = "cities"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=128)
    country: Country = ormar.ForeignKey(
        Country, related_name="cities", skip_reverse=True
    )


Country.update_forward_refs()


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@app.post("/", response_model=Country, status_code=status.HTTP_201_CREATED)
async def create_country(country: Country):  # if this is ormar
    result = await country.upsert()  # it's already initialized as ormar model
    return result


def test_payload():
    client = TestClient(app)
    with client as client:
        payload = {
            "name": "Thailand",
            "iso2": "TH",
            "iso3": "THA",
            "population": 23123123,
            "demonym": "Thai",
            "native_name": "Thailand",
        }
        resp = client.post("/", json=payload, headers={"application-type": "json"})
        # print(resp.content)
        assert resp.status_code == 201

        resp_country = Country(**resp.json())
        assert resp_country.name == "Thailand"
