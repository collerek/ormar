from typing import Dict, Optional

import ormar
import pydantic
import pytest
from pydantic import Json, PositiveInt, ValidationError

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class OverwriteTest(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="overwrites")

    id: int = ormar.Integer(primary_key=True)
    my_int: int = ormar.Integer(overwrite_pydantic_type=PositiveInt)
    constraint_dict: Json = ormar.JSON(
        overwrite_pydantic_type=Optional[Json[Dict[str, int]]]
    )  # type: ignore


class User(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="users")
    id: int = ormar.Integer(primary_key=True)
    email: str = ormar.String(
        max_length=255,
        unique=True,
        nullable=False,
        overwrite_pydantic_type=pydantic.EmailStr,
    )


create_test_database = init_tests(base_ormar_config)


def test_constraints():
    with pytest.raises(ValidationError, match="Input should be greater than 0"):
        OverwriteTest(my_int=-10)

    with pytest.raises(
        ValidationError,
        match="Input should be a valid integer, unable to parse string as an integer",
    ):
        OverwriteTest(my_int=10, constraint_dict={"aa": "ab"})

    with pytest.raises(
        ValidationError,
        match=(
            r"The email address is not valid. It must have exactly one @-sign|"
            r"An email address must have an @-sign"
        ),
    ):
        User(email="wrong")


@pytest.mark.asyncio
async def test_saving():
    async with base_ormar_config.database:
        await OverwriteTest(my_int=5, constraint_dict={"aa": 123}).save()

        test = await OverwriteTest.objects.get()
        assert test.my_int == 5
        assert test.constraint_dict == {"aa": 123}

        await User(email="test@as.eu").save()
        test = await User.objects.get()
        assert test.email == "test@as.eu"
