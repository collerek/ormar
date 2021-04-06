from typing import Optional

import databases
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Director(ormar.Model):
    class Meta:
        tablename = "directors"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="first_name")
    last_name: str = ormar.String(max_length=100, nullable=False, name="last_name")


class Movie(ormar.Model):
    class Meta:
        tablename = "movies"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="title")
    year: int = ormar.Integer()
    profit: float = ormar.Float()
    director: Optional[Director] = ormar.ForeignKey(Director)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_updating_selected_columns():
    async with database:
        director1 = await Director(name="Peter", last_name="Jackson").save()
        director2 = await Director(name="James", last_name="Cameron").save()

        lotr = await Movie(
            name="LOTR", year=2001, director=director1, profit=1.140
        ).save()

        lotr.name = "Lord of The Rings"
        lotr.year = 2003
        lotr.profit = 1.212

        await lotr.update(_columns=["name"])

        # before reload the field has current value even if not saved
        assert lotr.year == 2003

        lotr = await Movie.objects.get()
        assert lotr.name == "Lord of The Rings"
        assert lotr.year == 2001
        assert round(lotr.profit, 3) == 1.140
        assert lotr.director.pk == director1.pk

        lotr.year = 2003
        lotr.profit = 1.212
        lotr.director = director2

        await lotr.update(_columns=["year", "profit"])
        lotr = await Movie.objects.get()
        assert lotr.year == 2003
        assert round(lotr.profit, 3) == 1.212
        assert lotr.director.pk == director1.pk


@pytest.mark.asyncio
async def test_not_passing_columns_or_empty_list_saves_all():
    async with database:
        director = await Director(name="James", last_name="Cameron").save()
        terminator = await Movie(
            name="Terminator", year=1984, director=director, profit=0.078
        ).save()

        terminator.name = "Terminator 2"
        terminator.year = 1991
        terminator.profit = 0.520

        await terminator.update(_columns=[])

        terminator = await Movie.objects.get()
        assert terminator.name == "Terminator 2"
        assert terminator.year == 1991
        assert round(terminator.profit, 3) == 0.520

        terminator.name = "Terminator 3"
        terminator.year = 2003
        terminator.profit = 0.433

        await terminator.update()

        terminator = await terminator.load()
        assert terminator.name == "Terminator 3"
        assert terminator.year == 2003
        assert round(terminator.profit, 3) == 0.433
