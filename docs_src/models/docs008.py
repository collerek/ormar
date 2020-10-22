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

    id: ormar.Integer(name='child_id', primary_key=True)
    first_name: ormar.String(name='fname', max_length=100)
    last_name: ormar.String(name='lname', max_length=100)
    born_year: ormar.Integer(name='year_born', nullable=True)
