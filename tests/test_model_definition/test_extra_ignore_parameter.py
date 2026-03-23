import ormar
from ormar import Extra
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config(force_rollback=True)


class Child(ormar.Model):
    ormar_config = base_ormar_config.copy(
        tablename="children",
        extra=Extra.ignore,
    )

    id: int = ormar.Integer(name="child_id", primary_key=True)
    first_name: str = ormar.String(name="fname", max_length=100)
    last_name: str = ormar.String(name="lname", max_length=100)


create_test_database = init_tests(base_ormar_config)


def test_allow_extra_parameter():
    child = Child(first_name="Test", last_name="Name", extra_param="Unexpected")
    assert child.first_name == "Test"
    assert child.last_name == "Name"
    assert not hasattr(child, "extra_param")
