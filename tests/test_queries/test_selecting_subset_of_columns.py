import asyncio
import itertools
from typing import Optional, List

import databases
import pydantic
import pytest
import pytest_asyncio
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class NickNames(ormar.Model):
    class Meta:
        tablename = "nicks"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="hq_name")
    is_lame: bool = ormar.Boolean(nullable=True)


class NicksHq(ormar.Model):
    class Meta:
        tablename = "nicks_x_hq"
        metadata = metadata
        database = database


class HQ(ormar.Model):
    class Meta:
        tablename = "hqs"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="hq_name")
    nicks: List[NickNames] = ormar.ManyToMany(NickNames, through=NicksHq)


class Company(ormar.Model):
    class Meta:
        tablename = "companies"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="company_name")
    founded: int = ormar.Integer(nullable=True)
    hq: HQ = ormar.ForeignKey(HQ)


class Car(ormar.Model):
    class Meta:
        tablename = "cars"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    manufacturer: Optional[Company] = ormar.ForeignKey(Company)
    name: str = ormar.String(max_length=100)
    year: int = ormar.Integer(nullable=True)
    gearbox_type: str = ormar.String(max_length=20, nullable=True)
    gears: int = ormar.Integer(nullable=True)
    aircon_type: str = ormar.String(max_length=20, nullable=True)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True, scope="module")
async def sample_data(event_loop, create_test_database):
    async with database:
        nick1 = await NickNames.objects.create(name="Nippon", is_lame=False)
        nick2 = await NickNames.objects.create(name="EroCherry", is_lame=True)
        hq = await HQ.objects.create(name="Japan")
        await hq.nicks.add(nick1)
        await hq.nicks.add(nick2)

        toyota = await Company.objects.create(name="Toyota", founded=1937, hq=hq)

        await Car.objects.create(
            manufacturer=toyota,
            name="Corolla",
            year=2020,
            gearbox_type="Manual",
            gears=5,
            aircon_type="Manual",
        )
        await Car.objects.create(
            manufacturer=toyota,
            name="Yaris",
            year=2019,
            gearbox_type="Manual",
            gears=5,
            aircon_type="Manual",
        )
        await Car.objects.create(
            manufacturer=toyota,
            name="Supreme",
            year=2020,
            gearbox_type="Auto",
            gears=6,
            aircon_type="Auto",
        )


@pytest.mark.asyncio
async def test_selecting_subset():
    async with database:
        async with database.transaction(force_rollback=True):
            all_cars = (
                await Car.objects.select_related(["manufacturer__hq__nicks"])
                .fields(
                    [
                        "id",
                        "name",
                        "manufacturer__name",
                        "manufacturer__hq__name",
                        "manufacturer__hq__nicks__name",
                    ]
                )
                .all()
            )

            all_cars2 = (
                await Car.objects.select_related(["manufacturer__hq__nicks"])
                .fields(
                    {
                        "id": ...,
                        "name": ...,
                        "manufacturer": {
                            "name": ...,
                            "hq": {"name": ..., "nicks": {"name": ...}},
                        },
                    }
                )
                .all()
            )

            all_cars3 = (
                await Car.objects.select_related(["manufacturer__hq__nicks"])
                .fields(
                    {
                        "id": ...,
                        "name": ...,
                        "manufacturer": {
                            "name": ...,
                            "hq": {"name": ..., "nicks": {"name"}},
                        },
                    }
                )
                .all()
            )
            assert all_cars3 == all_cars

            for car in itertools.chain(all_cars, all_cars2):
                assert all(
                    getattr(car, x) is None
                    for x in ["year", "gearbox_type", "gears", "aircon_type"]
                )
                assert car.manufacturer.name == "Toyota"
                assert car.manufacturer.founded is None
                assert car.manufacturer.hq.name == "Japan"
                assert len(car.manufacturer.hq.nicks) == 2
                assert car.manufacturer.hq.nicks[0].is_lame is None

            all_cars = (
                await Car.objects.select_related("manufacturer")
                .fields("id")
                .fields(["name"])
                .all()
            )
            for car in all_cars:
                assert all(
                    getattr(car, x) is None
                    for x in ["year", "gearbox_type", "gears", "aircon_type"]
                )
                assert car.manufacturer.name == "Toyota"
                assert car.manufacturer.founded == 1937
                assert car.manufacturer.hq.name is None

            all_cars_check = await Car.objects.select_related("manufacturer").all()
            all_cars_with_whole_nested = (
                await Car.objects.select_related("manufacturer")
                .fields(["id", "name", "year", "gearbox_type", "gears", "aircon_type"])
                .fields({"manufacturer": ...})
                .all()
            )
            for car in itertools.chain(all_cars_check, all_cars_with_whole_nested):
                assert all(
                    getattr(car, x) is not None
                    for x in ["year", "gearbox_type", "gears", "aircon_type"]
                )
                assert car.manufacturer.name == "Toyota"
                assert car.manufacturer.founded == 1937

            all_cars_dummy = (
                await Car.objects.select_related("manufacturer")
                .fields(["id", "name", "year", "gearbox_type", "gears", "aircon_type"])
                # .fields({"manufacturer": ...})
                # .exclude_fields({"manufacturer": ...})
                .fields({"manufacturer": {"name"}})
                .exclude_fields({"manufacturer__founded"})
                .all()
            )

            assert all_cars_dummy[0].manufacturer.founded is None

            with pytest.raises(pydantic.error_wrappers.ValidationError):
                # cannot exclude mandatory model columns - company__name in this example
                await Car.objects.select_related("manufacturer").fields(
                    ["id", "name", "manufacturer__founded"]
                ).all()


@pytest.mark.asyncio
async def test_selecting_subset_of_through_model():
    async with database:
        car = (
            await Car.objects.select_related(["manufacturer__hq__nicks"])
            .fields(
                {
                    "id": ...,
                    "name": ...,
                    "manufacturer": {
                        "name": ...,
                        "hq": {"name": ..., "nicks": {"name": ...}},
                    },
                }
            )
            .exclude_fields("manufacturer__hq__nickshq")
            .get()
        )
        assert car.manufacturer.hq.nicks[0].nickshq is None

        car = (
            await Car.objects.select_related(["manufacturer__hq__nicks"])
            .fields(
                {
                    "id": ...,
                    "name": ...,
                    "manufacturer": {
                        "name": ...,
                        "hq": {"name": ..., "nicks": {"name": ...}},
                    },
                }
            )
            .exclude_fields({"manufacturer": {"hq": {"nickshq": ...}}})
            .get()
        )
        assert car.manufacturer.hq.nicks[0].nickshq is None

        car = (
            await Car.objects.select_related(["manufacturer__hq__nicks"])
            .fields(
                {
                    "id": ...,
                    "name": ...,
                    "manufacturer": {
                        "name": ...,
                        "hq": {"name": ..., "nicks": {"name": ...}},
                    },
                }
            )
            .exclude_fields("manufacturer__hq__nickshq__nick")
            .get()
        )
        assert car.manufacturer.hq.nicks[0].nickshq is not None
