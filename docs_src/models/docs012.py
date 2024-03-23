import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Course(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
    )

    id = ormar.Integer(primary_key=True)
    name = ormar.String(max_length=100)
    completed = ormar.Boolean(default=False)
