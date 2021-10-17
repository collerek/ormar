import enum

import databases
import pydantic
import pytest
import sqlalchemy
from pydantic import ValidationError

import ormar
from tests.settings import DATABASE_URL

metadata = sqlalchemy.MetaData()
database = databases.Database(DATABASE_URL)


class BaseMeta(ormar.ModelMeta):
    database = database
    metadata = metadata


class BaseModel(ormar.Model):
    class Meta:
        abstract = True

    id: int = ormar.Integer(primary_key=True)


class EnumExample(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"


class ModelExample(BaseModel):
    class Meta(BaseMeta):
        tablename = "examples"

    str_field: str = ormar.String(min_length=5, max_length=10, nullable=False)
    enum_field: str = ormar.String(
        max_length=1, nullable=False, choices=list(EnumExample)
    )

    @pydantic.validator("str_field")
    def validate_str_field(cls, v):
        if " " not in v:
            raise ValueError("must contain a space")
        return v


ModelExampleCreate = ModelExample.get_pydantic(exclude={"id"})


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
