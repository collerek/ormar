from typing import ForwardRef, Optional

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from starlette import status

import ormar
from tests.lifespan import init_tests, lifespan
from tests.settings import create_config

base_ormar_config = create_config()
app = FastAPI(lifespan=lifespan(base_ormar_config))


CityRef = ForwardRef("City")
CountryRef = ForwardRef("Country")


# models.py
class Country(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="countries")

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
    borders: list[Optional[CountryRef]] = ormar.ManyToMany(  # type: ignore
        CountryRef, nullable=True, skip_reverse=True
    )


class City(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="cities")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=128)
    country: Country = ormar.ForeignKey(
        Country, related_name="cities", skip_reverse=True
    )


Country.update_forward_refs()


create_test_database = init_tests(base_ormar_config)


@app.post("/", response_model=Country, status_code=status.HTTP_201_CREATED)
async def create_country(country: Country):  # if this is ormar
    result = await country.upsert()  # it's already initialized as ormar model
    return result


@pytest.mark.asyncio
async def test_payload():
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    async with client as client, LifespanManager(app):
        payload = {
            "name": "Thailand",
            "iso2": "TH",
            "iso3": "THA",
            "population": 23123123,
            "demonym": "Thai",
            "native_name": "Thailand",
        }
        resp = await client.post(
            "/", json=payload, headers={"application-type": "json"}
        )
        # print(resp.content)
        assert resp.status_code == 201

        resp_country = Country(**resp.json())
        assert resp_country.name == "Thailand"
