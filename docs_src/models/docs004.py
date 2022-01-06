import databases
import sqlalchemy

import ormar

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Course(ormar.Model):
    class Meta(
        ormar.ModelMeta
    ):  # note you don't have to subclass - but it's recommended for ide completion and mypy
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    completed: bool = ormar.Boolean(default=False)


print(Course.Meta.table.columns)
"""
Will produce:
['courses.id', 'courses.name', 'courses.completed']
"""
