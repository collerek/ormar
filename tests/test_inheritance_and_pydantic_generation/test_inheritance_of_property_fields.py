from pydantic import computed_field

import ormar
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class BaseFoo(ormar.Model):
    ormar_config = base_ormar_config.copy(abstract=True)

    name: str = ormar.String(max_length=100)

    @computed_field
    def prefixed_name(self) -> str:
        return "prefix_" + self.name


class Foo(BaseFoo):
    ormar_config = base_ormar_config.copy()

    @computed_field
    def double_prefixed_name(self) -> str:
        return "prefix2_" + self.name

    id: int = ormar.Integer(primary_key=True)


class Bar(BaseFoo):
    ormar_config = base_ormar_config.copy()

    @computed_field
    def prefixed_name(self) -> str:
        return "baz_" + self.name

    id: int = ormar.Integer(primary_key=True)


create_test_database = init_tests(base_ormar_config)


def test_property_fields_are_inherited():
    foo = Foo(name="foo")
    assert foo.prefixed_name == "prefix_foo"
    assert foo.model_dump() == {
        "name": "foo",
        "id": None,
        "double_prefixed_name": "prefix2_foo",
        "prefixed_name": "prefix_foo",
    }

    bar = Bar(name="bar")
    assert bar.prefixed_name == "baz_bar"
    assert bar.model_dump() == {"name": "bar", "id": None, "prefixed_name": "baz_bar"}
