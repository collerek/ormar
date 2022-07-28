import uuid

import databases
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

metadata = sqlalchemy.MetaData()
database = databases.Database(DATABASE_URL)


class MainMeta(ormar.ModelMeta):
    database = database
    metadata = metadata


class Human(ormar.Model):
    class Meta(MainMeta):
        pass

    id: uuid.UUID = ormar.UUID(
        primary_key=True, default=uuid.uuid4, uuid_format="string"
    )
    first_name: str = ormar.String(max_length=50)
    last_name: str = ormar.String(max_length=50)


class User(Human):
    class Meta(MainMeta):
        proxy = True

    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_method_proxy_models():
    async with database:
        await Human.objects.create(first_name="foo", last_name="bar")

        users = await User.objects.all()
        assert len(users) == 1
        assert users[0].full_name() == "foo bar"
