import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class ToDo(ormar.Model):
    class Meta:
        tablename = "todos"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    text: str = ormar.String(max_length=500)
    completed = ormar.Boolean(default=False)


# create multiple instances at once with bulk_create
await ToDo.objects.bulk_create(
    [
        ToDo(text="Buy the groceries."),
        ToDo(text="Call Mum.", completed=True),
        ToDo(text="Send invoices.", completed=True),
    ]
)

todoes = await ToDo.objects.all()
assert len(todoes) == 3
