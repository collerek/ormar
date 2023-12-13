import datetime

import databases
import pytest
import sqlalchemy

import ormar
from ormar import property_field
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Album(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename="albums",
        metadata=metadata,
        database=database,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    timestamp: datetime.datetime = ormar.DateTime(pydantic_only=True)

    @property_field
    def name10(self) -> str:
        return self.name + "_10"

    @property_field
    def name20(self) -> str:
        return self.name + "_20"

    @property
    def name30(self) -> str:
        return self.name + "_30"

    @property_field
    def name40(self) -> str:
        return self.name + "_40"


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

            assert album.name30 == "Hitchcock_30"

            album.timestamp = datetime.datetime.now()
            test_dict = album.dict()
            assert "timestamp" in test_dict
            assert test_dict["timestamp"] is not None
            assert test_dict.get("name10") == "Hitchcock_10"
            assert test_dict.get("name20") == "Hitchcock_20"
            assert test_dict.get("name40") == "Hitchcock_40"
            assert "name30" not in test_dict
