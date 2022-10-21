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

        await Movie(
            id=1, name="Lord of The Rings", year=2003, director=director1, profit=1.212
        ).upsert()

        with pytest.raises(ormar.NoMatch):
            await Movie.objects.get()

        await Movie(
            id=1, name="Lord of The Rings", year=2003, director=director1, profit=1.212
        ).upsert(__force_save__=True)
        lotr = await Movie.objects.get()
        assert lotr.year == 2003
        assert lotr.name == "Lord of The Rings"
