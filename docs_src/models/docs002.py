import databases
import sqlalchemy

import ormar

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Course(ormar.Model):
    # if you omit this parameter it will be created automatically
    # as class.__name__.lower()+'s' -> "courses" in this example
    __tablename__ = "my_courses"
    __database__ = database
    __metadata__ = metadata

    id = ormar.Integer(primary_key=True)
    name = ormar.String(length=100)
    completed = ormar.Boolean(default=False)
