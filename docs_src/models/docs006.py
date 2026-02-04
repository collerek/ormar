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
        # define your constraints in OrmarConfig of the model
        # it's a list that can contain multiple constraints
        # hera a combination of name and column will have to be unique in db
        constraints=[ormar.UniqueColumns("name", "completed")],
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    completed: bool = ormar.Boolean(default=False)
