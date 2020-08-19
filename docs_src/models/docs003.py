import databases
import sqlalchemy

import ormar

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Course(ormar.Model):
    __database__ = database
    __metadata__ = metadata

    id = ormar.Integer(primary_key=True)
    name = ormar.String(length=100)
    completed = ormar.Boolean(default=False)

print(Course.__pydantic_model__.__fields__)
"""
Will produce:
{'completed': ModelField(name='completed', 
                         type=bool, 
                         required=False, 
                         default=False),
 'id':        ModelField(name='id', 
                         type=Optional[int], 
                         required=False, 
                         default=None),
 'name':      ModelField(name='name', 
                         type=Optional[str], 
                         required=False, 
                         default=None)}
"""
