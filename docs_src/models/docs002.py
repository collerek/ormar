import databases
import sqlalchemy

import ormar

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Course(ormar.Model):
    class Meta:
        # if you omit this parameter it will be created automatically
        # as class.__name__.lower()+'s' -> "courses" in this example
        tablename = "my_courses"
        database = database
        metadata = metadata

    id: ormar.Integer(primary_key=True)
    name: ormar.String(max_length=100)
    completed: ormar.Boolean(default=False)
