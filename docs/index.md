# ormar
<p>
<a href="https://pypi.org/project/ormar">
    <img src="https://img.shields.io/pypi/v/ormar.svg" alt="Pypi version">
</a>
<a href="https://pypi.org/project/ormar">
    <img src="https://img.shields.io/pypi/pyversions/ormar.svg" alt="Pypi version">
</a>
<img src="https://github.com/collerek/ormar/workflows/build/badge.svg" alt="Build Status">
<a href="https://codecov.io/gh/collerek/ormar">
    <img src="https://codecov.io/gh/collerek/ormar/branch/master/graph/badge.svg" alt="Coverage">
</a>
<a href="https://www.codefactor.io/repository/github/collerek/ormar">
<img src="https://www.codefactor.io/repository/github/collerek/ormar/badge" alt="CodeFactor" />
</a>
<a href="https://app.codacy.com/manual/collerek/ormar?utm_source=github.com&utm_medium=referral&utm_content=collerek/oramr&utm_campaign=Badge_Grade_Dashboard">
<img src="https://api.codacy.com/project/badge/Grade/62568734f70f49cd8ea7a1a0b2d0c107" alt="Codacy" />
</a>
</p>

### Overview

The `ormar` package is an async mini ORM for Python, with support for **Postgres,
MySQL**, and **SQLite**. 

The main benefit of using `ormar` are:

*  getting an **async ORM that can be used with async frameworks** (fastapi, starlette etc.)
*  getting just **one model to maintain** - you don't have to maintain pydantic and other orm model (sqlalchemy, peewee, gino etc.)

The goal was to create a simple ORM that can be **used directly (as request and response models) with [`fastapi`][fastapi]** that bases it's data validation on pydantic.

Ormar - apart form obvious ORM in name - get it's name from ormar in swedish which means snakes, and ormar(e) in italian which means cabinet. 

And what's a better name for python ORM than snakes cabinet :)

### Documentation

Check out the [documentation][documentation] for details.

### Dependencies

Ormar is built with:

  * [`SQLAlchemy core`][sqlalchemy-core] for query building.
  * [`databases`][databases] for cross-database async support.
  * [`pydantic`][pydantic] for data validation.
  * `typing_extensions` for python 3.6 - 3.7

### Migrations

Because ormar is built on SQLAlchemy core, you can use [`alembic`][alembic] to provide
database migrations.


**ormar is still under development:** 
We recommend pinning any dependencies (with i.e. `ormar~=0.5.2`)

### Quick Start

**Note**: Use `ipython` to try this from the console, since it supports `await`.

```python
import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Album(ormar.Model):
    class Meta:
        tablename = "album"
        metadata = metadata
        database = database
    
    # note that type hints are optional so 
    # id = ormar.Integer(primary_key=True) 
    # is also valid
    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Track(ormar.Model):
    class Meta:
        tablename = "track"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    album: Optional[Album] = ormar.ForeignKey(Album)
    title: str = ormar.String(max_length=100)
    position: int = ormar.Integer()


# Create some records to work with.
malibu = await Album.objects.create(name="Malibu")
await Track.objects.create(album=malibu, title="The Bird", position=1)
await Track.objects.create(album=malibu, title="Heart don't stand a chance", position=2)
await Track.objects.create(album=malibu, title="The Waters", position=3)

# alternative creation of object divided into 2 steps
fantasies = Album(name="Fantasies")
await fantasies.save()
await Track.objects.create(album=fantasies, title="Help I'm Alive", position=1)
await Track.objects.create(album=fantasies, title="Sick Muse", position=2)


# Fetch an instance, without loading a foreign key relationship on it.
track = await Track.objects.get(title="The Bird")

# We have an album instance, but it only has the primary key populated
print(track.album)       # Album(id=1) [sparse]
print(track.album.pk)    # 1
print(track.album.name)  # None

# Load the relationship from the database
await track.album.load()
assert track.album.name == "Malibu"

# This time, fetch an instance, loading the foreign key relationship.
track = await Track.objects.select_related("album").get(title="The Bird")
assert track.album.name == "Malibu"

# By default you also get a second side of the relation 
# constructed as lowercase source model name +'s' (tracks in this case)
# you can also provide custom name with parameter related_name
album = await Album.objects.select_related("tracks").all()
assert len(album.tracks) == 3

# Fetch instances, with a filter across an FK relationship.
tracks = Track.objects.filter(album__name="Fantasies")
assert len(tracks) == 2

# Fetch instances, with a filter and operator across an FK relationship.
tracks = Track.objects.filter(album__name__iexact="fantasies")
assert len(tracks) == 2

# Limit a query
tracks = await Track.objects.limit(1).all()
assert len(tracks) == 1
```

## Ormar Specification

### QuerySet methods

*  `create(**kwargs): -> Model`
*  `get(**kwargs): -> Model`
*  `get_or_create(**kwargs) -> Model`
*  `update(each: bool = False, **kwargs) -> int`
*  `update_or_create(**kwargs) -> Model`
*  `bulk_create(objects: List[Model]) -> None`
*  `bulk_update(objects: List[Model], columns: List[str] = None) -> None`
*  `delete(each: bool = False, **kwargs) -> int`
*  `all(self, **kwargs) -> List[Optional[Model]]`
*  `filter(**kwargs) -> QuerySet`
*  `exclude(**kwargs) -> QuerySet`
*  `select_related(related: Union[List, str]) -> QuerySet`
*  `prefetch_related(related: Union[List, str]) -> QuerySet`
*  `limit(limit_count: int) -> QuerySet`
*  `offset(offset: int) -> QuerySet`
*  `count() -> int`
*  `exists() -> bool`
*  `fields(columns: Union[List, str, set, dict]) -> QuerySet`
*  `exclude_fields(columns: Union[List, str, set, dict]) -> QuerySet`
*  `order_by(columns:Union[List, str]) -> QuerySet`


#### Relation types

*  One to many  - with `ForeignKey(to: Model)`
*  Many to many - with `ManyToMany(to: Model, through: Model)`

#### Model fields types

Available Model Fields (with required args - optional ones in docs):

* `String(max_length)`
* `Text()`
* `Boolean()`
* `Integer()`
* `Float()`
* `Date()`
* `Time()`
* `DateTime()`
* `JSON()`
* `BigInteger()`
* `Decimal(scale, precision)`
* `UUID()`
* `ForeignKey(to)`
* `ManyToMany(to, through)`

### Available fields options
The following keyword arguments are supported on all field types.

  * `primary_key: bool`
  * `nullable: bool`
  * `default: Any`
  * `server_default: Any`
  * `index: bool`
  * `unique: bool`
  * `choices: typing.Sequence`
  * `name: str`

All fields are required unless one of the following is set:

  * `nullable` - Creates a nullable column. Sets the default to `None`.
  * `default` - Set a default value for the field.
  * `server_default` - Set a default value for the field on server side (like sqlalchemy's `func.now()`).
  * `primary key` with `autoincrement` - When a column is set to primary key and autoincrement is set on this column. 
Autoincrement is set by default on int primary keys. 



[sqlalchemy-core]: https://docs.sqlalchemy.org/en/latest/core/
[databases]: https://github.com/encode/databases
[pydantic]: https://pydantic-docs.helpmanual.io/
[encode/orm]: https://github.com/encode/orm/
[alembic]: https://alembic.sqlalchemy.org/en/latest/
[fastapi]: https://fastapi.tiangolo.com/
[documentation]: https://collerek.github.io/ormar/