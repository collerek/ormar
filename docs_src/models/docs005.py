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

print(Course.__model_fields__)
"""
Will produce:
{
'id':   {'name': 'id', 
         'primary_key': True, 
         'autoincrement': True, 
         'nullable': False, 
         'default': None, 
         'server_default': None, 
         'index': None, 
         'unique': None, 
         'pydantic_only': False}, 
'name':  {'name': 'name', 
          'primary_key': False, 
          'autoincrement': False, 
          'nullable': True, 
          'default': None, 
          'server_default': None, 
          'index': None, 
          'unique': None, 
          'pydantic_only': False, 
          'length': 100}, 
'completed': {'name': 'completed', 
              'primary_key': False, 
              'autoincrement': False, 
              'nullable': True, 
              'default': False, 
              'server_default': None, 
              'index': None, 
              'unique': None, 
              'pydantic_only': False}
}
"""
