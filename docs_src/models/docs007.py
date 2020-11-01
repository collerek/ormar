import databases
import sqlalchemy

import ormar

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Course(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    completed: bool = ormar.Boolean(default=False)


course = Course(name="Painting for dummies", completed=False)
await course.save()

await Course.objects.create(name="Painting for dummies", completed=False)
