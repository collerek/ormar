from typing import Dict, Optional, Union

import ormar
import sqlalchemy
from ormar import DatabaseConnection
from sqlalchemy.ext.asyncio import create_async_engine

database = DatabaseConnection("sqlite+aiosqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()
engine = create_async_engine(database.url)


class Department(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
        engine=engine,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Course(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
        engine=engine,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    completed: bool = ormar.Boolean(default=False)
    department: Optional[Union[Department, Dict]] = ormar.ForeignKey(Department)


department = Department(name="Science")

# set up a relation with actual Model instance
course = Course(name="Math", completed=False, department=department)

# set up  relation with only related model pk value
course2 = Course(name="Math II", completed=False, department=department.pk)

# set up a relation with dictionary corresponding to related model
course3 = Course(name="Math III", completed=False, department=department.model_dump())

# explicitly set up None
course4 = Course(name="Math III", completed=False, department=None)
