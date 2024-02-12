import ormar

from tests.settings import create_config
from tests.lifespan import init_tests


base_ormar_config = create_config()


class NewTestModel(ormar.Model):
    ormar_config = base_ormar_config.copy()

    a: int = ormar.Integer(primary_key=True)
    b: str = ormar.String(max_length=1)
    c: str = ormar.String(max_length=1)
    d: str = ormar.String(max_length=1)
    e: str = ormar.String(max_length=1)
    f: str = ormar.String(max_length=1)


create_test_database = init_tests(base_ormar_config)


def test_model_field_order():
    TestCreate = NewTestModel.get_pydantic(exclude={"a"})
    assert list(TestCreate.model_fields.keys()) == ["b", "c", "d", "e", "f"]
