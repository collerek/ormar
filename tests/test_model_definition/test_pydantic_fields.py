import random
from typing import Optional

import databases
import pytest
import sqlalchemy
from pydantic import BaseModel, Field, HttpUrl, PaymentCardNumber

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

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=200)
    url: HttpUrl = "https://www.example.com"  # type: ignore
    number: Optional[PaymentCardNumber]


CARD_NUMBERS = [
    "123456789007",
    "123456789015",
    "123456789023",
    "123456789031",
    "123456789049",
]


def get_number():
    return random.choice(CARD_NUMBERS)


class ModelTest2(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=200)
    url: HttpUrl = "https://www.example2.com"  # type: ignore
    number: PaymentCardNumber = Field(default_factory=get_number)


class PydanticTest(BaseModel):
    aa: str
    bb: int


class ModelTest3(ormar.Model):
    class Meta(BaseMeta):
        pass

    def __init__(self, **kwargs):
        kwargs["number"] = get_number()
        kwargs["pydantic_test"] = PydanticTest(aa="random", bb=42)
        super().__init__(**kwargs)

    @classmethod
    def construct(cls, **kwargs):
        kwargs["number"] = get_number()
        kwargs["pydantic_test"] = PydanticTest(aa="random", bb=42)
        return super().construct(**kwargs)

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=200)
    url: HttpUrl = "https://www.example3.com"  # type: ignore
    number: PaymentCardNumber
    pydantic_test: PydanticTest


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
        assert test.url == "https://www.example.com"
        assert test.number is None
        test.number = "123456789015"

        test.url = "https://www.sdta.ada.pt"
        assert test.url == "https://www.sdta.ada.pt"

        await test.save()
        test_check = await ModelTest.objects.get()

        assert test_check.name == "Test"
        assert test_check.url == "https://www.example.com"
        assert test_check.number is None


@pytest.mark.asyncio
async def test_default_factory_for_pydantic_fields():
    async with database:
        test = ModelTest2(name="Test2", number="4000000000000002")
        assert test.name == "Test2"
        assert test.url == "https://www.example2.com"
        assert test.number == "4000000000000002"

        test.url = "http://www.sdta.ada.pt"
        assert test.url == "http://www.sdta.ada.pt"

        await test.save()
        test_check = await ModelTest2.objects.get()

        assert test_check.name == "Test2"
        assert test_check.url == "https://www.example2.com"
        assert test_check.number in CARD_NUMBERS
        assert test_check.number != test.number


@pytest.mark.asyncio
async def test_init_setting_for_pydantic_fields():
    async with database:
        test = ModelTest3(name="Test3")
        assert test.name == "Test3"
        assert test.url == "https://www.example3.com"
        assert test.pydantic_test.bb == 42

        test.url = "http://www.sdta.ada.pt"
        assert test.url == "http://www.sdta.ada.pt"

        await test.save()
        test_check = await ModelTest3.objects.get()

        assert test_check.name == "Test3"
        assert test_check.url == "https://www.example3.com"
        assert test_check.number in CARD_NUMBERS
        assert test_check.pydantic_test.aa == "random"
