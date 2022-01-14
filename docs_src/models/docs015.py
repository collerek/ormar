import databases
import sqlalchemy

import ormar
from ormar import property_field

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Course(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    completed: bool = ormar.Boolean(default=False)

    @property_field
    def prefixed_name(self):
        return "custom_prefix__" + self.name
