import databases
import sqlalchemy

import ormar

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Department(ormar.Model):
    __database__ = database
    __metadata__ = metadata

    id = ormar.Integer(primary_key=True)
    name = ormar.String(length=100)


class Course(ormar.Model):
    __database__ = database
    __metadata__ = metadata

    id = ormar.Integer(primary_key=True)
    name = ormar.String(length=100)
    completed = ormar.Boolean(default=False)
    department = ormar.ForeignKey(Department)


department = Department(name="Science")
course = Course(name="Math", completed=False, department=department)

print('name' in course.__dict__)
# False <- property name is not stored on Course instance
print(course.name)
# Math <- value returned from underlying pydantic model
print('department' in course.__dict__)
# False <- related model is not stored on Course instance
print(course.department)
# Department(id=None, name='Science') <- Department model
# returned from AliasManager
print(course.department.name)
# Science