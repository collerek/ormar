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


department = Department(name='Science')

# set up a relation with actual Model instance
course = Course(name='Math', completed=False, department=department)

# set up  relation with only related model pk value
course2 = Course(name='Math II', completed=False, department=department.pk)

# set up a relation with dictionary corresponding to related model
course3 = Course(name='Math III', completed=False, department=department.dict())

# explicitly set up None
course4 = Course(name='Math III', completed=False, department=None)
