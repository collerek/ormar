import databases
import ormar
import pytest
import sqlalchemy

from tests.settings import DATABASE_URL

metadata = sqlalchemy.MetaData()
database = databases.Database(DATABASE_URL)


base_ormar_config = ormar.OrmarConfig(
    metadata=metadata,
    database=database,
)


class NewTestModel(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
    )

    a: int = ormar.Integer(primary_key=True)
    b: str = ormar.String(max_length=1)
    c: str = ormar.String(max_length=1)
    d: str = ormar.String(max_length=1)
    e: str = ormar.String(max_length=1)
    f: str = ormar.String(max_length=1)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


def test_model_field_order():
    TestCreate = NewTestModel.get_pydantic(exclude={"a"})
    assert list(TestCreate.model_fields.keys()) == ["b", "c", "d", "e", "f"]
