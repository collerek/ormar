import asyncio

import databases
import ormar
import sqlalchemy
from examples import create_drop_database
from ormar import pre_update

DATABASE_URL = "sqlite:///test.db"

ormar_base_config = ormar.OrmarConfig(
    database=databases.Database(DATABASE_URL), metadata=sqlalchemy.MetaData()
)


class Album(ormar.Model):
    ormar_config = ormar_base_config.copy(
        tablename="albums",
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    is_best_seller: bool = ormar.Boolean(default=False)
    play_count: int = ormar.Integer(default=0)


@pre_update(Album)
async def before_update(sender, instance, **kwargs):
    if instance.play_count > 50 and not instance.is_best_seller:
        instance.is_best_seller = True


@create_drop_database(base_config=ormar_base_config)
async def run_query():
    # here album.play_count ans is_best_seller get default values
    album = await Album.objects.create(name="Venice")
    assert not album.is_best_seller
    assert album.play_count == 0

    album.play_count = 30
    # here a trigger is called but play_count is too low
    await album.update()
    assert not album.is_best_seller

    album.play_count = 60
    await album.update()
    assert album.is_best_seller


asyncio.run(run_query())
