# Selecting subset of columns

To select only chosen columns of your model you can use following functions.

* `fields(columns: Union[List, str, set, dict]) -> QuerySet`
* `exclude_fields(columns: Union[List, str, set, dict]) -> QuerySet`


* `QuerysetProxy`
    * `QuerysetProxy.fields(columns: Union[List, str, set, dict])` method
    * `QuerysetProxy.exclude_fields(columns: Union[List, str, set, dict])` method

## fields

`fields(columns: Union[List, str, set, dict]) -> QuerySet`

With `fields()` you can select subset of model columns to limit the data load.

!!!note 
    Note that `fields()` and `exclude_fields()` works both for main models (on
    normal queries like `get`, `all` etc.)
    as well as `select_related` and `prefetch_related` models (with nested notation).

Given a sample data like following:

```python
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


```

You can select specified fields by passing a `str, List[str], Set[str] or dict` with
nested definition.

To include related models use
notation `{related_name}__{column}[__{optional_next} etc.]`.

```python hl_lines="1"
all_cars = await Car.objects.select_related('manufacturer').fields(['id', 'name', 'manufacturer__name']).all()
for car in all_cars:
    # excluded columns will yield None
    assert all(getattr(car, x) is None for x in ['year', 'gearbox_type', 'gears', 'aircon_type'])
    # included column on related models will be available, pk column is always included
    # even if you do not include it in fields list
    assert car.manufacturer.name == 'Toyota'
    # also in the nested related models - you cannot exclude pk - it's always auto added
    assert car.manufacturer.founded is None
```

`fields()` can be called several times, building up the columns to select.

If you include related models into `select_related()` call but you won't specify columns
for those models in fields

- implies a list of all fields for those nested models.

```python hl_lines="1"
all_cars = await Car.objects.select_related('manufacturer').fields('id').fields(
    ['name']).all()
# all fiels from company model are selected
assert all_cars[0].manufacturer.name == 'Toyota'
assert all_cars[0].manufacturer.founded == 1937
```

!!!warning 
    Mandatory fields cannot be excluded as it will raise `ValidationError`, to
    exclude a field it has to be nullable.

You cannot exclude mandatory model columns - `manufacturer__name` in this example.

```python
await Car.objects.select_related('manufacturer').fields(
    ['id', 'name', 'manufacturer__founded']).all()
# will raise pydantic ValidationError as company.name is required
```

!!!tip 
    Pk column cannot be excluded - it's always auto added even if not explicitly
    included.

You can also pass fields to include as dictionary or set.

To mark a field as included in a dictionary use it's name as key and ellipsis as value.

To traverse nested models use nested dictionaries.

To include fields at last level instead of nested dictionary a set can be used.

To include whole nested model specify model related field name and ellipsis.

Below you can see examples that are equivalent:

```python
# 1. like in example above
await Car.objects.select_related('manufacturer').fields(['id', 'name', 'manufacturer__name']).all()

# 2. to mark a field as required use ellipsis
await Car.objects.select_related('manufacturer').fields({'id': ...,
                                                         'name': ...,
                                                         'manufacturer': {
                                                             'name': ...}
                                                         }).all()

# 3. to include whole nested model use ellipsis
await Car.objects.select_related('manufacturer').fields({'id': ...,
                                                         'name': ...,
                                                         'manufacturer': ...
                                                         }).all()

# 4. to specify fields at last nesting level you can also use set - equivalent to 2. above
await Car.objects.select_related('manufacturer').fields({'id': ...,
                                                         'name': ...,
                                                         'manufacturer': {'name'}
                                                         }).all()

# 5. of course set can have multiple fields
await Car.objects.select_related('manufacturer').fields({'id': ...,
                                                         'name': ...,
                                                         'manufacturer': {'name', 'founded'}
                                                         }).all()

# 6. you can include all nested fields but it will be equivalent of 3. above which is shorter
await Car.objects.select_related('manufacturer').fields({'id': ...,
                                                         'name': ...,
                                                         'manufacturer': {'id', 'name', 'founded'}
                                                         }).all()

```

!!!note 
    All methods that do not return the rows explicitly returns a QueySet instance so
    you can chain them together

    So operations like `filter()`, `select_related()`, `limit()` and `offset()` etc. can be chained.
    
    Something like `Track.objects.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`

## exclude_fields

`exclude_fields(columns: Union[List, str, set, dict]) -> QuerySet`

With `exclude_fields()` you can select subset of model columns that will be excluded to
limit the data load.

It's the opposite of `fields()` method so check documentation above to see what options
are available.

Especially check above how you can pass also nested dictionaries and sets as a mask to
exclude fields from whole hierarchy.

!!!note 
    Note that `fields()` and `exclude_fields()` works both for main models (on
    normal queries like `get`, `all` etc.)
    as well as `select_related` and `prefetch_related` models (with nested notation).

Below you can find few simple examples:

```python hl_lines="47 48 60 61 67"
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
all_cars = await Car.objects.select_related('manufacturer').exclude_fields(
    ['year', 'gearbox_type', 'gears', 'aircon_type', 'company__founded']).all()
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
all_cars = await Car.objects.select_related('manufacturer').exclude_fields('year').exclude_fields(
    ['gear', 'gearbox_type']).all()
# all fiels from company model are selected
assert all_cars[0].manufacturer.name == 'Toyota'
assert all_cars[0].manufacturer.founded == 1937

# cannot exclude mandatory model columns - company__name in this example - note usage of dict/set this time
await Car.objects.select_related('manufacturer').exclude_fields([{'company': {'name'}}]).all()
# will raise pydantic ValidationError as company.name is required

```

!!!warning 
    Mandatory fields cannot be excluded as it will raise `ValidationError`, to
    exclude a field it has to be nullable.

!!!tip 
    Pk column cannot be excluded - it's always auto added even if explicitly
    excluded.

!!!note 
    All methods that do not return the rows explicitly returns a QueySet instance so
    you can chain them together

    So operations like `filter()`, `select_related()`, `limit()` and `offset()` etc. can be chained.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`


## QuerysetProxy methods

When access directly the related `ManyToMany` field as well as `ReverseForeignKey`
returns the list of related models.

But at the same time it exposes subset of QuerySet API, so you can filter, create,
select related etc related models directly from parent model.

### fields

Works exactly the same as [fields](./#fields) function above but allows you to select columns from related
objects from other side of the relation.

!!!tip 
    To read more about `QuerysetProxy` visit [querysetproxy][querysetproxy] section

### exclude_fields

Works exactly the same as [exclude_fields](./#exclude_fields) function above but allows you to select columns from related
objects from other side of the relation.

!!!tip 
    To read more about `QuerysetProxy` visit [querysetproxy][querysetproxy] section


[querysetproxy]: ../relations/queryset-proxy.md
