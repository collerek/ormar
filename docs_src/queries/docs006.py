import databases
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Company(ormar.Model):
    class Meta:
        tablename = "companies"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    founded: int = ormar.Integer(nullable=True)


class Car(ormar.Model):
    class Meta:
        tablename = "cars"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    manufacturer = ormar.ForeignKey(Company)
    name: str = ormar.String(max_length=100)
    year: int = ormar.Integer(nullable=True)
    gearbox_type: str = ormar.String(max_length=20, nullable=True)
    gears: int = ormar.Integer(nullable=True)
    aircon_type: str = ormar.String(max_length=20, nullable=True)


# build some sample data
toyota = await Company.objects.create(name="Toyota", founded=1937)
await Car.objects.create(manufacturer=toyota, name="Corolla", year=2020, gearbox_type='Manual', gears=5,
                         aircon_type='Manual')
await Car.objects.create(manufacturer=toyota, name="Yaris", year=2019, gearbox_type='Manual', gears=5,
                         aircon_type='Manual')
await Car.objects.create(manufacturer=toyota, name="Supreme", year=2020, gearbox_type='Auto', gears=6,
                         aircon_type='Auto')

# select manufacturer but only name - to include related models use notation {model_name}__{column}
all_cars = await Car.objects.select_related('manufacturer').fields(['id', 'name', 'company__name']).all()
for car in all_cars:
    # excluded columns will yield None
    assert all(getattr(car, x) is None for x in ['year', 'gearbox_type', 'gears', 'aircon_type'])
    # included column on related models will be available, pk column is always included
    # even if you do not include it in fields list
    assert car.manufacturer.name == 'Toyota'
    # also in the nested related models - you cannot exclude pk - it's always auto added
    assert car.manufacturer.founded is None

# fields() can be called several times, building up the columns to select
# models selected in select_related but with no columns in fields list implies all fields
all_cars = await Car.objects.select_related('manufacturer').fields('id').fields(
    ['name']).all()
# all fiels from company model are selected
assert all_cars[0].manufacturer.name == 'Toyota'
assert all_cars[0].manufacturer.founded == 1937

# cannot exclude mandatory model columns - company__name in this example
await Car.objects.select_related('manufacturer').fields(['id', 'name', 'company__founded']).all()
# will raise pydantic ValidationError as company.name is required
