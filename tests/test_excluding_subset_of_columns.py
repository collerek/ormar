from typing import Optional

import databases
import pydantic
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Company(ormar.Model):
    class Meta:
        tablename = "companies"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False)
    founded: int = ormar.Integer(nullable=True)


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
    gears: int = ormar.Integer(nullable=True, name="gears_number")
    aircon_type: str = ormar.String(max_length=20, nullable=True)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_selecting_subset():
    async with database:
        async with database.transaction(force_rollback=True):
            toyota = await Company.objects.create(name="Toyota", founded=1937)
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

            all_cars = (
                await Car.objects.select_related("manufacturer")
                .exclude_fields(
                    [
                        "gearbox_type",
                        "gears",
                        "aircon_type",
                        "year",
                        "manufacturer__founded",
                    ]
                )
                .all()
            )
            for car in all_cars:
                assert all(
                    getattr(car, x) is None
                    for x in ["year", "gearbox_type", "gears", "aircon_type"]
                )
                assert car.manufacturer.name == "Toyota"
                assert car.manufacturer.founded is None

            all_cars = (
                await Car.objects.select_related("manufacturer")
                .exclude_fields(
                    {
                        "gearbox_type": ...,
                        "gears": ...,
                        "aircon_type": ...,
                        "year": ...,
                        "manufacturer": {"founded": ...},
                    }
                )
                .all()
            )
            all_cars2 = (
                await Car.objects.select_related("manufacturer")
                .exclude_fields(
                    {
                        "gearbox_type": ...,
                        "gears": ...,
                        "aircon_type": ...,
                        "year": ...,
                        "manufacturer": {"founded"},
                    }
                )
                .all()
            )

            assert all_cars == all_cars2

            for car in all_cars:
                assert all(
                    getattr(car, x) is None
                    for x in ["year", "gearbox_type", "gears", "aircon_type"]
                )
                assert car.manufacturer.name == "Toyota"
                assert car.manufacturer.founded is None

            all_cars = (
                await Car.objects.select_related("manufacturer")
                .exclude_fields("year")
                .exclude_fields(["gearbox_type", "gears"])
                .exclude_fields("aircon_type")
                .all()
            )
            for car in all_cars:
                assert all(
                    getattr(car, x) is None
                    for x in ["year", "gearbox_type", "gears", "aircon_type"]
                )
                assert car.manufacturer.name == "Toyota"
                assert car.manufacturer.founded == 1937

            all_cars_check = await Car.objects.select_related("manufacturer").all()
            for car in all_cars_check:
                assert all(
                    getattr(car, x) is not None
                    for x in ["year", "gearbox_type", "gears", "aircon_type"]
                )
                assert car.manufacturer.name == "Toyota"
                assert car.manufacturer.founded == 1937

            all_cars_check2 = (
                await Car.objects.select_related("manufacturer")
                .fields(["id", "name", "manufacturer"])
                .exclude_fields("manufacturer__founded")
                .all()
            )
            for car in all_cars_check2:
                assert all(
                    getattr(car, x) is None
                    for x in ["year", "gearbox_type", "gears", "aircon_type"]
                )
                assert car.manufacturer.name == "Toyota"
                assert car.manufacturer.founded is None

            with pytest.raises(pydantic.error_wrappers.ValidationError):
                # cannot exclude mandatory model columns - company__name in this example
                await Car.objects.select_related("manufacturer").exclude_fields(
                    ["manufacturer__name"]
                ).all()
