import enum

import ormar
import pytest
from pydantic import ValidationError, field_validator

from tests.settings import create_config
from tests.lifespan import init_tests


base_ormar_config = create_config()


class EnumExample(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"


class ModelExample(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="examples")

    id: int = ormar.Integer(primary_key=True)
    str_field: str = ormar.String(min_length=5, max_length=10, nullable=False)
    enum_field: str = ormar.Enum(nullable=False, enum_class=EnumExample)

    @field_validator("str_field")
    def validate_str_field(cls, v):
        if " " not in v:
            raise ValueError("must contain a space")
        return v


ModelExampleCreate = ModelExample.get_pydantic(exclude={"id"})


create_test_database = init_tests(base_ormar_config)


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
