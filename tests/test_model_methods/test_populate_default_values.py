import databases
import ormar
import sqlalchemy
from sqlalchemy import text

from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


base_ormar_config = ormar.OrmarConfig(
    metadata=metadata,
    database=database,
)


class Task(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="tasks")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(
        max_length=255, minimum=0, server_default=text("Default Name"), nullable=False
    )
    points: int = ormar.Integer(
        default=0, minimum=0, server_default=text("0"), nullable=False
    )
    score: int = ormar.Integer(default=5)


def test_populate_default_values():
    new_kwargs = {
        "id": None,
        "name": "",
        "points": 0,
    }
    result = Task.populate_default_values(new_kwargs)

    assert result["id"] is None
    assert result["name"] == ""
    assert result["points"] == 0
    assert result["score"] == 5
