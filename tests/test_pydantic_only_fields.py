import datetime

import databases
import pytest
import sqlalchemy
from pydantic import validator

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Album(ormar.Model):
    class Meta:
        tablename = "albums"
        metadata = metadata
        database = database
        include_props_in_dict = True
        include_props_in_fields = True

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    timestamp: datetime.datetime = ormar.DateTime(pydantic_only=True)

    @property
    def name10(self) -> str:
        return self.name + "_10"

    @validator("name")
    def test(cls, v):
        return v


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_pydantic_only_fields():
    async with database:
        async with database.transaction(force_rollback=True):
            album = await Album.objects.create(name="Hitchcock")
            assert album.pk is not None
            assert album.saved
            assert album.timestamp is None

            album = await Album.objects.exclude_fields("timestamp").get()
            assert album.timestamp is None

            album = await Album.objects.fields({"name", "timestamp"}).get()
            assert album.timestamp is None

            test_dict = album.dict()
            assert "timestamp" in test_dict
            assert test_dict["timestamp"] is None

            album.timestamp = datetime.datetime.now()
            test_dict = album.dict()
            assert "timestamp" in test_dict
            assert test_dict["timestamp"] is not None
            assert test_dict.get("name10") == "Hitchcock_10"

            Album.Meta.include_props_in_dict = False
            test_dict = album.dict()
            assert "timestamp" in test_dict
            assert test_dict["timestamp"] is not None
            # key is still there as now it's a field
            assert test_dict["name10"] is None
