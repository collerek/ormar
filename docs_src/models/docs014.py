import ormar
import pydantic
import sqlalchemy
from ormar import DatabaseConnection

database = DatabaseConnection("sqlite+aiosqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Course(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    completed: bool = ormar.Boolean(default=False)
    non_db_field: str = pydantic.Field(max_length=100)
