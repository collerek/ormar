import databases
import sqlalchemy

import ormar

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Course(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id = ormar.Integer(primary_key=True)
    name = ormar.String(max_length=100)
    completed= ormar.Boolean(default=False)


print(Course.__fields__)
"""
Will produce:
{'id':        ModelField(name='id', 
                         type=Optional[int], 
                         required=False, 
                         default=None),
 'name':      ModelField(name='name', 
                         type=Optional[str], 
                         required=False, 
                         default=None),
'completed':  ModelField(name='completed', 
                         type=bool, 
                         required=False, 
                         default=False)}
"""
