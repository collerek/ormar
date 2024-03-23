from typing import Optional

import ormar
import pydantic
import pytest

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Company(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="companies")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False)
    founded: int = ormar.Integer(nullable=True)


class Car(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="cars")

    id: int = ormar.Integer(primary_key=True)
    manufacturer: Optional[Company] = ormar.ForeignKey(Company)
    name: str = ormar.String(max_length=100)
    year: int = ormar.Integer(nullable=True)
    gearbox_type: str = ormar.String(max_length=20, nullable=True)
    gears: int = ormar.Integer(nullable=True, name="gears_number")
    aircon_type: str = ormar.String(max_length=20, nullable=True)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_selecting_subset():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
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

            with pytest.raises(pydantic.ValidationError):
                # cannot exclude mandatory model columns - company__name in this example
                await Car.objects.select_related("manufacturer").exclude_fields(
                    ["manufacturer__name"]
                ).all()


@pytest.mark.asyncio
async def test_excluding_nested_lists_in_dump():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            toyota = await Company.objects.create(name="Toyota", founded=1937)
            car1 = await Car.objects.create(
                manufacturer=toyota,
                name="Corolla",
                year=2020,
                gearbox_type="Manual",
                gears=5,
                aircon_type="Manual",
            )
            car2 = await Car.objects.create(
                manufacturer=toyota,
                name="Yaris",
                year=2019,
                gearbox_type="Manual",
                gears=5,
                aircon_type="Manual",
            )
            manufacturer = await Company.objects.select_related("cars").get(
                name="Toyota"
            )
            assert manufacturer.model_dump() == {
                "cars": [
                    {
                        "aircon_type": "Manual",
                        "gearbox_type": "Manual",
                        "gears": 5,
                        "id": car1.id,
                        "name": "Corolla",
                        "year": 2020,
                    },
                    {
                        "aircon_type": "Manual",
                        "gearbox_type": "Manual",
                        "gears": 5,
                        "id": car2.id,
                        "name": "Yaris",
                        "year": 2019,
                    },
                ],
                "founded": 1937,
                "id": toyota.id,
                "name": "Toyota",
            }
            assert manufacturer.model_dump(exclude_list=True) == {
                "founded": 1937,
                "id": toyota.id,
                "name": "Toyota",
            }
