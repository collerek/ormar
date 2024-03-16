import asyncio

import databases
import ormar
import sqlalchemy
from examples import create_drop_database

DATABASE_URL = "sqlite:///test.db"

ormar_base_config = ormar.OrmarConfig(
    database=databases.Database(DATABASE_URL),
    metadata=sqlalchemy.MetaData(),
)


class Owner(ormar.Model):
    ormar_config = ormar_base_config.copy(tablename="owners")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Toy(ormar.Model):
    ormar_config = ormar_base_config.copy(tablename="toys")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    owner: Owner = ormar.ForeignKey(Owner)


@create_drop_database(base_config=ormar_base_config)
async def run_query():
    # build some sample data
    aphrodite = await Owner.objects.create(name="Aphrodite")
    hermes = await Owner.objects.create(name="Hermes")
    zeus = await Owner.objects.create(name="Zeus")

    await Toy.objects.create(name="Toy 4", owner=zeus)
    await Toy.objects.create(name="Toy 5", owner=hermes)
    await Toy.objects.create(name="Toy 2", owner=aphrodite)
    await Toy.objects.create(name="Toy 1", owner=zeus)
    await Toy.objects.create(name="Toy 3", owner=aphrodite)
    await Toy.objects.create(name="Toy 6", owner=hermes)


asyncio.run(run_query())
