import datetime

import ormar
import pydantic
import pytest
from pydantic import computed_field

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Album(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="albums")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    timestamp: datetime.datetime = pydantic.Field(default=None)  # type: ignore

    @computed_field
    def name10(self) -> str:
        return self.name + "_10"

    @computed_field
    def name20(self) -> str:
        return self.name + "_20"

    @property
    def name30(self) -> str:
        return self.name + "_30"

    @computed_field
    def name40(self) -> str:
        return self.name + "_40"


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_pydantic_only_fields():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            album = await Album.objects.create(name="Hitchcock")
            assert album.pk is not None
            assert album.saved
            assert album.timestamp is None

            album = await Album.objects.exclude_fields("timestamp").get()
            assert album.timestamp is None

            album = await Album.objects.fields({"name", "timestamp"}).get()
            assert album.timestamp is None

            test_dict = album.model_dump()
            assert "timestamp" in test_dict
            assert test_dict["timestamp"] is None

            assert album.name30 == "Hitchcock_30"

            album.timestamp = datetime.datetime.now()
            test_dict = album.model_dump()
            assert "timestamp" in test_dict
            assert test_dict["timestamp"] is not None
            assert test_dict.get("name10") == "Hitchcock_10"
            assert test_dict.get("name20") == "Hitchcock_20"
            assert test_dict.get("name40") == "Hitchcock_40"
            assert "name30" not in test_dict
