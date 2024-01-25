import databases
import ormar
import sqlalchemy
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Owner(ormar.Model):
    class Meta:
        tablename = "owners"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Toy(ormar.Model):
    class Meta:
        tablename = "toys"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    owner: Owner = ormar.ForeignKey(Owner)


# build some sample data
aphrodite = await Owner.objects.create(name="Aphrodite")
hermes = await Owner.objects.create(name="Hermes")
zeus = await Owner.objects.create(name="Zeus")

await Toy.objects.create(name="Toy 4", owner=zeus)
await Toy.objects.create(name="Toy 5", owner=hermes)
await Toy.objects.create(name="Toy 2", owner=aphrodite)
await Toy.objects.create(name="Toy 1", owner=zeus)
await Toy.objects.create(name="Toy 3", owner=aphrodite)
await Toy.objects.create(name="Toy 6", owner=hermes)
