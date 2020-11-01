import databases
import sqlalchemy

import ormar

database = databases.Database("sqlite:///test.db", force_rollback=True)
metadata = sqlalchemy.MetaData()


class Child(ormar.Model):
    class Meta:
        tablename = "children"
        metadata = metadata
        database = database

    id: int = ormar.Integer(name="child_id", primary_key=True)
    first_name: str = ormar.String(name="fname", max_length=100)
    last_name: str = ormar.String(name="lname", max_length=100)
    born_year: int = ormar.Integer(name="year_born", nullable=True)
