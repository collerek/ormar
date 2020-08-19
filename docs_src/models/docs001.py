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
