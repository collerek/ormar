from typing import Optional

import databases
import ormar
import pytest
import sqlalchemy
from sqlalchemy import create_engine

from tests.settings import DATABASE_URL

db = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class PrimaryModel(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        metadata=metadata,
        database=db,
        tablename="primary_models",
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=255, index=True)
    some_text: str = ormar.Text()
    # NOTE: Removing nullable=True makes the test pass.
    some_other_text: Optional[str] = ormar.Text(nullable=True)


class SecondaryModel(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        metadata=metadata,
        database=db,
        tablename="secondary_models",
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    primary_model: PrimaryModel = ormar.ForeignKey(
        PrimaryModel, related_name="secondary_models"
    )


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_create_models():
    async with db:
        async with db.transaction(force_rollback=True):
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
