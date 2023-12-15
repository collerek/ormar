import enum

import databases
import pytest
import sqlalchemy
from pydantic import ValidationError, field_validator

import ormar
from tests.settings import DATABASE_URL

metadata = sqlalchemy.MetaData()
database = databases.Database(DATABASE_URL)


base_ormar_config = ormar.OrmarConfig(
    metadata=metadata,
    database=database,
)


class BaseModel(ormar.Model):
    ormar_config = ormar.OrmarConfig(abstract=True)

    id: int = ormar.Integer(primary_key=True)
    str_field: str = ormar.String(min_length=5, max_length=10, nullable=False)

    @field_validator("str_field")
    def validate_str_field(cls, v):
        if " " not in v:
            raise ValueError("must contain a space")
        return v


class EnumExample(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"


class ModelExample(BaseModel):
    ormar_config = base_ormar_config.copy(tablename="examples")

    enum_field: str = ormar.Enum(enum_class=EnumExample, nullable=False)


ModelExampleCreate = ModelExample.get_pydantic(exclude={"id"})


def test_ormar_validator():
    ModelExample(str_field="a aaaaaa", enum_field="A")
    with pytest.raises(ValidationError) as e:
        ModelExample(str_field="aaaaaaa", enum_field="A")
    assert "must contain a space" in str(e)
    with pytest.raises(ValidationError) as e:
        ModelExample(str_field="a aaaaaaa", enum_field="Z")
    assert "Input should be 'A', 'B' or 'C'" in str(e)


def test_pydantic_validator():
    ModelExampleCreate(str_field="a aaaaaa", enum_field="A")
    with pytest.raises(ValidationError) as e:
        ModelExampleCreate(str_field="aaaaaaa", enum_field="A")
    assert "must contain a space" in str(e)
    with pytest.raises(ValidationError) as e:
        ModelExampleCreate(str_field="a aaaaaaa", enum_field="Z")
    assert "Input should be 'A', 'B' or 'C'" in str(e)
