import asyncio

import ormar
import sqlalchemy
from examples import create_drop_database
from ormar import DatabaseConnection
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "sqlite+aiosqlite:///queries_docs009.db"

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
    # 1. like in example above
    await Car.objects.select_related("manufacturer").fields(
        ["id", "name", "manufacturer__name"]
    ).all()

    # 2. to mark a field as required use ellipsis
    await Car.objects.select_related("manufacturer").fields(
        {"id": ..., "name": ..., "manufacturer": {"name": ...}}
    ).all()

    # 3. to include whole nested model use ellipsis
    await Car.objects.select_related("manufacturer").fields(
        {"id": ..., "name": ..., "manufacturer": ...}
    ).all()

    # 4. to specify fields at last nesting level you can also use set
    # - equivalent to 2. above
    await Car.objects.select_related("manufacturer").fields(
        {"id": ..., "name": ..., "manufacturer": {"name"}}
    ).all()

    # 5. of course set can have multiple fields
    await Car.objects.select_related("manufacturer").fields(
        {"id": ..., "name": ..., "manufacturer": {"name", "founded"}}
    ).all()

    # 6. you can include all nested fields,
    # but it will be equivalent of 3. above which is shorter
    await Car.objects.select_related("manufacturer").fields(
        {"id": ..., "name": ..., "manufacturer": {"id", "name", "founded"}}
    ).all()


asyncio.run(run_query())
