import enum

import databases
import pydantic
import pytest
import sqlalchemy
from pydantic import ValidationError
from pydantic.class_validators import make_generic_validator


import ormar
from tests.settings import DATABASE_URL

metadata = sqlalchemy.MetaData()
database = databases.Database(DATABASE_URL)


class BaseMeta(ormar.ModelMeta):
    database = database
    metadata = metadata


class EnumExample(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"


class ModelExample(ormar.Model):
    class Meta(ormar.ModelMeta):
        database = database
        metadata = metadata
        tablename = "examples"

    id: int = ormar.Integer(primary_key=True)
    str_field: str = ormar.String(min_length=5, max_length=10, nullable=False)
    enum_field: str = ormar.String(
        max_length=1, nullable=False, choices=list(EnumExample)
    )

    @pydantic.validator("str_field")
    def validate_str_field(cls, v):
        if " " not in v:
            raise ValueError("must contain a space")
        return v


def validate_str_field(cls, v):
    if " " not in v:
        raise ValueError("must contain a space")
    return v


def validate_choices(cls, v):
    if v not in list(EnumExample):
        raise ValueError(f"{v} is not in allowed choices: {list(EnumExample)}")
    return v


ModelExampleCreate = ModelExample.get_pydantic(exclude={"id"})
ModelExampleCreate.__fields__["str_field"].validators.append(
    make_generic_validator(validate_str_field)
)
ModelExampleCreate.__fields__["enum_field"].validators.append(
    make_generic_validator(validate_choices)
)


def test_ormar_validator():
    ModelExample(str_field="a aaaaaa", enum_field="A")
    with pytest.raises(ValidationError) as e:
        ModelExample(str_field="aaaaaaa", enum_field="A")
    assert "must contain a space" in str(e)
    with pytest.raises(ValidationError) as e:
        ModelExample(str_field="a aaaaaaa", enum_field="Z")
    assert "not in allowed choices" in str(e)


def test_pydantic_validator():
    ModelExampleCreate(str_field="a aaaaaa", enum_field="A")
    with pytest.raises(ValidationError) as e:
        ModelExampleCreate(str_field="aaaaaaa", enum_field="A")
    assert "must contain a space" in str(e)
    with pytest.raises(ValidationError) as e:
        ModelExampleCreate(str_field="a aaaaaaa", enum_field="Z")
    assert "not in allowed choices" in str(e)
