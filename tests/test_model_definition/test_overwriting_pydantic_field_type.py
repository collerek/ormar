from typing import Dict, Optional

import databases
import ormar
import pytest
import sqlalchemy
from pydantic import Json, PositiveInt, ValidationError

from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class OverwriteTest(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename="overwrites",
        metadata=metadata,
        database=database,
    )

    id: int = ormar.Integer(primary_key=True)
    my_int: int = ormar.Integer(overwrite_pydantic_type=PositiveInt)
    constraint_dict: Json = ormar.JSON(overwrite_pydantic_type=Optional[Json[Dict[str, int]]])  # type: ignore


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


def test_constraints():
    with pytest.raises(ValidationError) as e:
        OverwriteTest(my_int=-10)
    assert "Input should be greater than 0" in str(e.value)

    with pytest.raises(ValidationError) as e:
        OverwriteTest(my_int=10, constraint_dict={"aa": "ab"})
    assert (
        "Input should be a valid integer, unable to parse string as an integer"
        in str(e.value)
    )


@pytest.mark.asyncio
async def test_saving():
    async with database:
        await OverwriteTest(my_int=5, constraint_dict={"aa": 123}).save()

        test = await OverwriteTest.objects.get()
        assert test.my_int == 5
        assert test.constraint_dict == {"aa": 123}
