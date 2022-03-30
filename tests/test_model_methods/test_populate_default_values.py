import databases
import sqlalchemy
from sqlalchemy import text

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    database = database
    metadata = metadata


class Task(ormar.Model):
    class Meta(BaseMeta):
        tablename = "tasks"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(
        max_length=255, minimum=0, server_default=text("Default Name"), nullable=False
    )
    points: int = ormar.Integer(
        default=0, minimum=0, server_default=text("0"), nullable=False
    )


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
