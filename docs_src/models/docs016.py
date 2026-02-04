import ormar
import pydantic
import sqlalchemy
from ormar import DatabaseConnection
from sqlalchemy.ext.asyncio import create_async_engine

database = DatabaseConnection("sqlite+aiosqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()
engine = create_async_engine(database.url)


class Course(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
        engine=engine,
    )

    model_config = pydantic.ConfigDict(frozen=True)

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    completed: bool = ormar.Boolean(default=False)
