from typing import Optional

import databases
import ormar
import sqlalchemy

DATABASE_URL = "sqlite:///test.db"

ormar_base_config = ormar.OrmarConfig(
    database=databases.Database(DATABASE_URL), metadata=sqlalchemy.MetaData()
)


class Department(ormar.Model):
    ormar_config = ormar_base_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Course(ormar.Model):
    ormar_config = ormar_base_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    completed: bool = ormar.Boolean(default=False)
    department: Optional[Department] = ormar.ForeignKey(
        Department, related_name="my_courses"
    )


department = Department(name="Science")
course = Course(name="Math", completed=False, department=department)

print(department.my_courses[0])
# Will produce:
# Course(id=None,
#        name='Math',
#        completed=False,
#        department=Department(id=None, name='Science'))
