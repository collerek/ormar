import databases
import sqlalchemy

import ormar

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Course(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id: ormar.Integer(primary_key=True)
    name: ormar.String(max_length=100)
    completed: ormar.Boolean(default=False)

c1 = Course()
