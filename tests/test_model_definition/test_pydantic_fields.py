from typing import Optional

import databases
import pytest
import sqlalchemy
from pydantic import EmailStr, HttpUrl, ValidationError

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class Test(ormar.Model):
    class Meta(BaseMeta):
        pass

    def __init__(self, **kwargs):
        # you need to pop non - db fields as ormar will complain that it's unknown field
        email = kwargs.pop("email", self.__fields__["email"].get_default())
        url = kwargs.pop("url", self.__fields__["url"].get_default())
        super().__init__(**kwargs)
        self.email = email
        self.url = url

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=200)
    email: Optional[EmailStr]  # field optional - default to None
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
        test = Test(name="Test", email="aka@go2.com")
        assert test.name == "Test"
        assert test.email == "aka@go2.com"
        assert test.url == "www.example.com"

        test.email = "sdta@ada.pt"
        assert test.email == "sdta@ada.pt"

        await test.save()
        test_check = await Test.objects.get()

        assert test_check.name == "Test"
        assert test_check.email is None
        assert test_check.url == "www.example.com"

        # TODO add validate assignment to pydantic config
        # test_check.email = 1
