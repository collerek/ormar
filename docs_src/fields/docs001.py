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


department = Department(name='Science')
course = Course(name='Math', completed=False, department=department)

print(department.courses[0])
# Will produce:
# Course(id=None,
#        name='Math',
#        completed=False,
#        department=Department(id=None, name='Science'))
