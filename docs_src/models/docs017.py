import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Course(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
        # define your constraints in Meta class of the model
        # it's a list that can contain multiple constraints
        # hera a combination of name and column will have a compound index in the db
        constraints=[ormar.IndexColumns("name", "completed")],
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    completed: bool = ormar.Boolean(default=False)
