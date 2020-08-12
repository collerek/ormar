import databases
import sqlalchemy

import orm

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Course(orm.Model):
    # if you omit this parameter it will be created automatically
    # as class.__name__.lower()+'s' -> "courses" in this example
    __tablename__ = "my_courses"
    __database__ = database
    __metadata__ = metadata

    id = orm.Integer(primary_key=True)
    name = orm.String(length=100)
    completed = orm.Boolean(default=False)
