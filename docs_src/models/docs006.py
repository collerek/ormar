import databases
import sqlalchemy

import orm

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Department(orm.Model):
    __database__ = database
    __metadata__ = metadata

    id = orm.Integer(primary_key=True)
    name = orm.String(length=100)


class Course(orm.Model):
    __database__ = database
    __metadata__ = metadata

    id = orm.Integer(primary_key=True)
    name = orm.String(length=100)
    completed = orm.Boolean(default=False)
    department = orm.ForeignKey(Department)


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
# returned from RelationshipManager
print(course.department.name)
# Science