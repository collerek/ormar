import asyncio

import ormar
import sqlalchemy
from examples import create_drop_database
from ormar import DatabaseConnection
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "sqlite+aiosqlite:///queries_docs006.db"

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


asyncio.run(run_query())
