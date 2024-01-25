import databases
import ormar
import sqlalchemy
from ormar import Extra

from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Child(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename="children",
        metadata=metadata,
        database=database,
        extra=Extra.ignore,
    )

    id: int = ormar.Integer(name="child_id", primary_key=True)
    first_name: str = ormar.String(name="fname", max_length=100)
    last_name: str = ormar.String(name="lname", max_length=100)


def test_allow_extra_parameter():
    child = Child(first_name="Test", last_name="Name", extra_param="Unexpected")
    assert child.first_name == "Test"
    assert child.last_name == "Name"
    assert not hasattr(child, "extra_param")
