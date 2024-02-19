import datetime

import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Course(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
        # define your constraints in OrmarConfig of the model
        # it's a list that can contain multiple constraints
        # hera a combination of name and column will have a level check in the db
        constraints=[
            ormar.CheckColumns("start_time < end_time", name="date_check"),
        ],
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    start_date: datetime.date = ormar.Date()
    end_date: datetime.date = ormar.Date()
