import asyncio

import ormar
import sqlalchemy
from examples import create_drop_database
from ormar import DatabaseConnection
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "sqlite+aiosqlite:///queries_docs008.db"

database = DatabaseConnection(DATABASE_URL)
metadata = sqlalchemy.MetaData()
engine = create_async_engine(DATABASE_URL)

ormar_base_config = ormar.OrmarConfig(
    database=database,
    metadata=metadata,
    engine=engine,
)


class Company(ormar.Model):
    ormar_config = ormar_base_config.copy(tablename="companies")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    founded: int = ormar.Integer(nullable=True)


class Car(ormar.Model):
    ormar_config = ormar_base_config.copy(tablename="cars")

    id: int = ormar.Integer(primary_key=True)
    manufacturer = ormar.ForeignKey(Company)
    name: str = ormar.String(max_length=100)
    year: int = ormar.Integer(nullable=True)
    gearbox_type: str = ormar.String(max_length=20, nullable=True)
    gears: int = ormar.Integer(nullable=True)
    aircon_type: str = ormar.String(max_length=20, nullable=True)


@create_drop_database(base_config=ormar_base_config)
async def run_query():
    # build some sample data
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

    # select manufacturer but only name,
    # to include related models use notation {model_name}__{column}
    all_cars = (
        await Car.objects.select_related("manufacturer")
        .exclude_fields(
            ["year", "gearbox_type", "gears", "aircon_type", "manufacturer__founded"]
        )
        .all()
    )
    for car in all_cars:
        # excluded columns will yield None
        assert all(
            getattr(car, x) is None
            for x in ["year", "gearbox_type", "gears", "aircon_type"]
        )
        # included column on related models will be available,
        # pk column is always included
        # even if you do not include it in fields list
        assert car.manufacturer.name == "Toyota"
        # also in the nested related models -
        # you cannot exclude pk - it's always auto added
        assert car.manufacturer.founded is None

    # fields() can be called several times,
    # building up the columns to select,
    # models selected in select_related
    # but with no columns in fields list implies all fields
    all_cars = (
        await Car.objects.select_related("manufacturer")
        .exclude_fields("year")
        .exclude_fields(["gear", "gearbox_type"])
        .all()
    )
    # all fiels from company model are selected
    assert all_cars[0].manufacturer.name == "Toyota"
    assert all_cars[0].manufacturer.founded == 1937

    # cannot exclude mandatory model columns -
    # manufacturer__name in this example - note usage of dict/set this time
    try:
        await Car.objects.select_related("manufacturer").exclude_fields(
            {"manufacturer": {"name"}}
        ).all()
    except ValidationError:
        # will raise pydantic ValidationError as company.name is required
        pass


asyncio.run(run_query())
