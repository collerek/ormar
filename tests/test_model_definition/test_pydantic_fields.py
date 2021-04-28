from typing import Optional

import databases
import pytest
import sqlalchemy
from pydantic import HttpUrl

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class ModelTest(ormar.Model):
    class Meta(BaseMeta):
        pass

    def __init__(self, **kwargs):
        # you need to pop non - db fields as ormar will complain that it's unknown field
        url = kwargs.pop("url", self.__fields__["url"].get_default())
        super().__init__(**kwargs)
        self.url = url

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=200)
    url: HttpUrl = "www.example.com"  # field with default


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_working_with_pydantic_fields():
    async with database:
        test = ModelTest(name="Test")
        assert test.name == "Test"
        assert test.url == "www.example.com"

        test.url = "www.sdta.ada.pt"
        assert test.url == "www.sdta.ada.pt"

        await test.save()
        test_check = await ModelTest.objects.get()

        assert test_check.name == "Test"
        assert test_check.url == "www.example.com"

        # TODO add validate assignment to pydantic config
        # test_check.email = 1
