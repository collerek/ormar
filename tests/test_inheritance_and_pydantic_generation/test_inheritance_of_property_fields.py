import databases
import pytest
import sqlalchemy
import sqlalchemy as sa

import ormar
from tests.settings import DATABASE_URL

metadata = sa.MetaData()
database = databases.Database(DATABASE_URL)


class BaseFoo(ormar.Model):
    class Meta:
        abstract = True

    name: str = ormar.String(max_length=100)

    @ormar.property_field
    def prefixed_name(self) -> str:
        return "prefix_" + self.name


class Foo(BaseFoo):
    class Meta:
        metadata = metadata
        database = database

    @ormar.property_field
    def double_prefixed_name(self) -> str:
        return "prefix2_" + self.name

    id: int = ormar.Integer(primary_key=True)


class Bar(BaseFoo):
    class Meta:
        metadata = metadata
        database = database

    @ormar.property_field
    def prefixed_name(self) -> str:
        return "baz_" + self.name

    id: int = ormar.Integer(primary_key=True)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


def test_property_fields_are_inherited():
    foo = Foo(name="foo")
    assert foo.prefixed_name == "prefix_foo"
    assert foo.dict() == {
        "name": "foo",
        "id": None,
        "double_prefixed_name": "prefix2_foo",
        "prefixed_name": "prefix_foo",
    }

    bar = Bar(name="bar")
    assert bar.prefixed_name == "baz_bar"
    assert bar.dict() == {"name": "bar", "id": None, "prefixed_name": "baz_bar"}
