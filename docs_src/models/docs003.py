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
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    completed: bool = ormar.Boolean(default=False)


print(Course.model_fields)
"""
Will produce:
{'id':        Field(name='id', 
                         type=Optional[int], 
                         required=False, 
                         default=None),
 'name':      Field(name='name', 
                         type=Optional[str], 
                         required=False, 
                         default=None),
'completed':  Field(name='completed', 
                         type=bool, 
                         required=False, 
                         default=False)}
"""
