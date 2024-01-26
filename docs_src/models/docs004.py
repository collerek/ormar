import databases
import ormar
import sqlalchemy

DATABASE_URL = "sqlite:///test.db"

ormar_base_config = ormar.OrmarConfig(
    database=databases.Database(DATABASE_URL), metadata=sqlalchemy.MetaData()
)


class Course(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename="courses",
        database=databases.Database(DATABASE_URL),
        metadata=sqlalchemy.MetaData(),
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    completed: bool = ormar.Boolean(default=False)


print(Course.ormar_config.table.columns)
"""
Will produce:
ImmutableColumnCollection(courses.id, courses.name, courses.completed)
"""
