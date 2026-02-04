import ormar
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
        # if you omit this parameter it will be created automatically
        # as class.__name__.lower()+'s' -> "courses" in this example
        tablename="my_courses",
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    completed: bool = ormar.Boolean(default=False)
