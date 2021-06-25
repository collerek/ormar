import datetime
import uuid

import databases
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

metadata = sqlalchemy.MetaData()
database = databases.Database(DATABASE_URL)


class BaseMeta(ormar.ModelMeta):
    database = database
    metadata = metadata


class BaseModel(ormar.Model):
    class Meta(ormar.ModelMeta):
        abstract = True

    id: uuid.UUID = ormar.UUID(
        primary_key=True, default=uuid.uuid4, uuid_format="string"
    )
    created_at: datetime.datetime = ormar.DateTime(default=datetime.datetime.utcnow())
    updated_at: datetime.datetime = ormar.DateTime(default=datetime.datetime.utcnow())


class Member(BaseModel):
    class Meta(BaseMeta):
        tablename = "members"

    first_name: str = ormar.String(max_length=50)
    last_name: str = ormar.String(max_length=50)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


def test_model_structure():
    assert "id" in BaseModel.__fields__
    assert "id" in BaseModel.Meta.model_fields
    assert BaseModel.Meta.model_fields["id"].has_default()
    assert BaseModel.__fields__["id"].default_factory is not None

    assert "id" in Member.__fields__
    assert "id" in Member.Meta.model_fields
    assert Member.Meta.model_fields["id"].has_default()
    assert Member.__fields__["id"].default_factory is not None


@pytest.mark.asyncio
async def test_fields_inherited_with_default():
    async with database:
        await Member(first_name="foo", last_name="bar").save()
        await Member.objects.create(first_name="foo", last_name="bar")
