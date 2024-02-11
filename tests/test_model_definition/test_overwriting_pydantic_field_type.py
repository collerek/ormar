from typing import Dict, Optional

import ormar
import pytest
from pydantic import Json, PositiveInt, ValidationError

from tests.settings import create_config
from tests.lifespan import init_tests


base_ormar_config = create_config()


class OverwriteTest(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="overwrites")

    id: int = ormar.Integer(primary_key=True)
    my_int: int = ormar.Integer(overwrite_pydantic_type=PositiveInt)
    constraint_dict: Json = ormar.JSON(
        overwrite_pydantic_type=Optional[Json[Dict[str, int]]]
    )  # type: ignore


create_test_database = init_tests(base_ormar_config)


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
    async with base_ormar_config.database:
        await OverwriteTest(my_int=5, constraint_dict={"aa": 123}).save()

        test = await OverwriteTest.objects.get()
        assert test.my_int == 5
        assert test.constraint_dict == {"aa": 123}
