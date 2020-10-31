from typing import Optional

import databases
import sqlalchemy

import ormar

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Department(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id = ormar.Integer(primary_key=True)
    name = ormar.String(max_length=100)


class Course(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id = ormar.Integer(primary_key=True)
    name = ormar.String(max_length=100)
    completed= ormar.Boolean(default=False)
    department= ormar.ForeignKey(Department)
