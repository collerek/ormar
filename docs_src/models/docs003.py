import ormar
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
