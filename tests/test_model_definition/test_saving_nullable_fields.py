from typing import Optional

import ormar
import pytest

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class PrimaryModel(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="primary_models")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=255, index=True)
    some_text: str = ormar.Text()
    # NOTE: Removing nullable=True makes the test pass.
    some_other_text: Optional[str] = ormar.Text(nullable=True)


class SecondaryModel(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="secondary_models")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    primary_model: PrimaryModel = ormar.ForeignKey(
        PrimaryModel, related_name="secondary_models"
    )


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_create_models():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            primary = await PrimaryModel(
                name="Foo", some_text="Bar", some_other_text="Baz"
            ).save()
            assert primary.id == 1

            secondary = await SecondaryModel(name="Foo", primary_model=primary).save()
            assert secondary.id == 1
            assert secondary.primary_model.id == 1

            secondary = await SecondaryModel.objects.get()
            assert secondary.name == "Foo"
            await secondary.update(name="Updated")
            assert secondary.name == "Updated"
