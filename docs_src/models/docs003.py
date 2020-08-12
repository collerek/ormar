import databases
import sqlalchemy

import orm

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Course(orm.Model):
    __database__ = database
    __metadata__ = metadata

    id = orm.Integer(primary_key=True)
    name = orm.String(length=100)
    completed = orm.Boolean(default=False)

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
