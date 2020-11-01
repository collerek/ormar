import databases
import sqlalchemy

import ormar

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Course(ormar.Model):
    class Meta(ormar.ModelMeta):
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    completed: bool = ormar.Boolean(default=False)


print({x: v.__dict__ for x, v in Course.Meta.model_fields.items()})
"""
Will produce:
{'completed': mappingproxy({'autoincrement': False,
                            'choices': set(),
                            'column_type': Boolean(),
                            'default': False,
                            'index': False,
                            'name': 'completed',
                            'nullable': True,
                            'primary_key': False,
                            'pydantic_only': False,
                            'server_default': None,
                            'unique': False}),
 'id': mappingproxy({'autoincrement': True,
                     'choices': set(),
                     'column_type': Integer(),
                     'default': None,
                     'ge': None,
                     'index': False,
                     'le': None,
                     'maximum': None,
                     'minimum': None,
                     'multiple_of': None,
                     'name': 'id',
                     'nullable': False,
                     'primary_key': True,
                     'pydantic_only': False,
                     'server_default': None,
                     'unique': False}),
 'name': mappingproxy({'allow_blank': False,
                       'autoincrement': False,
                       'choices': set(),
                       'column_type': String(length=100),
                       'curtail_length': None,
                       'default': None,
                       'index': False,
                       'max_length': 100,
                       'min_length': None,
                       'name': 'name',
                       'nullable': False,
                       'primary_key': False,
                       'pydantic_only': False,
                       'regex': None,
                       'server_default': None,
                       'strip_whitespace': False,
                       'unique': False})}
"""
