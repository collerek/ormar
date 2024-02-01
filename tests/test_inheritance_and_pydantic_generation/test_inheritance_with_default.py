import datetime
import uuid

import ormar
import pytest

from tests.settings import create_config
from tests.lifespan import init_tests


base_ormar_config = create_config()


class BaseModel(ormar.Model):
    ormar_config = base_ormar_config.copy(abstract=True)

    id: uuid.UUID = ormar.UUID(
        primary_key=True, default=uuid.uuid4, uuid_format="string"
    )
    created_at: datetime.datetime = ormar.DateTime(default=datetime.datetime.utcnow())
    updated_at: datetime.datetime = ormar.DateTime(default=datetime.datetime.utcnow())


class Member(BaseModel):
    ormar_config = base_ormar_config.copy(tablename="members")

    first_name: str = ormar.String(max_length=50)
    last_name: str = ormar.String(max_length=50)


create_test_database = init_tests(base_ormar_config)


def test_model_structure():
    assert "id" in BaseModel.model_fields
    assert "id" in BaseModel.ormar_config.model_fields
    assert BaseModel.ormar_config.model_fields["id"].has_default()
    assert BaseModel.model_fields["id"].default_factory is not None

    assert "id" in Member.model_fields
    assert "id" in Member.ormar_config.model_fields
    assert Member.ormar_config.model_fields["id"].has_default()
    assert Member.model_fields["id"].default_factory is not None


@pytest.mark.asyncio
async def test_fields_inherited_with_default():
    async with base_ormar_config.database:
        await Member(first_name="foo", last_name="bar").save()
        await Member.objects.create(first_name="foo", last_name="bar")
