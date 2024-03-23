# Migration to 0.20.0 based on pydantic 2.X.X

Version 0.20.0 provides support for pydantic v2.X.X that provides significant speed boost (validation and serialization is written in rust) and cleaner api for developers,
at the same time it drops support for pydantic v.1.X.X. There are changes in `ormar` interface corresponding to changes made in `pydantic`.

## Breaking changes

Migration to version >= 0.20.0 requires several changes in order to work properly.

## `ormar` Model configuration

Instead of defining a `Meta` class now each of the ormar models require an ormar_config parameter that is an instance of the `OrmarConfig` class.
Note that the attribute must be named `ormar_config` and be an instance of the config class.

```python
import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()

# ormar < 0.20
class Album(ormar.Model):
    class Meta:
        database = database
        metadata = metadata
        tablename = "albums"
    

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    favorite: bool = ormar.Boolean(default=False)

# ormar >= 0.20
class AlbumV20(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
        tablename="albums_v20"
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    favorite: bool = ormar.Boolean(default=False)
```

### `OrmarConfig` api/ parameters

The `ormar_config` expose the same set of settings as `Meta` class used to provide.
That means that you can use any of the following parameters initializing the config:

```python
metadata: Optional[sqlalchemy.MetaData]
database: Optional[databases.Database]
engine: Optional[sqlalchemy.engine.Engine]
tablename: Optional[str]
order_by: Optional[List[str]]
abstract: bool
exclude_parent_fields: Optional[List[str]]
queryset_class: Type[QuerySet]
extra: Extra
constraints: Optional[List[ColumnCollectionConstraint]]
```

### `BaseMeta` equivalent - best practice

Note that to reduce the duplication of code and ease of development it's still recommended to create a base config and provide each of the models with a copy.
OrmarConfig provides a convenient `copy` method for that purpose. 

The `copy` method accepts the same parameters as `OrmarConfig` init, so you can overwrite if needed, but by default it will return already existing attributes, except for: `tablename`, `order_by` and `constraints` which by default are cleared.

```python hl_lines="5-8 11 20"
import databases
import ormar
import sqlalchemy

base_ormar_config = ormar.OrmarConfig(
    database=databases.Database("sqlite:///db.sqlite"),
    metadata=sqlalchemy.MetaData()
)

class AlbumV20(ormar.Model):
    ormar_config = base_ormar_config.copy(
        tablename="albums_v20"
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)

    
class TrackV20(ormar.Model):
    ormar_config = base_ormar_config.copy(
        tablename="tracks_v20"
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
```

## `choices` Field parameter is no longer supported.

Before version 0.20 you could provide `choices` parameter to any existing ormar Field to limit the accepted values.
This functionality was dropped, and you should use `ormar.Enum` field that was designed for this purpose. 
If you want to keep the database field type (i.e. an Integer field) you can always write a custom validator.

```python
import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()

# ormar < 0.20
class Artist(ormar.Model):
    class Meta:
        database = database
        metadata = metadata
    

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    country: str = ormar.String(default=False, max_length=50, choices=["UK", "US", "Vietnam", "Colombia"])

# ormar >= 0.20
from enum import Enum

class Country(str, Enum):
    UK = "UK"
    US = "US"
    VIETNAM = "Vietnam"
    COLOMBIA = "Colombia"

class ArtistV20(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
        tablename="artists_v20"
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    country: Country = ormar.Enum(enum_class=Country)
```


## `pydantic_only` Field parameter is no longer supported

`pydantic_only` fields were already deprecated and are removed in v 0.20. Ormar allows defining pydantic fields as in ordinary pydantic model.

```python
import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()

# ormar < 0.20
class Dish(ormar.Model):
    class Meta:
        database = database
        metadata = metadata
        tablename = "dishes"
    

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    cook: str = ormar.String(max_length=40, pydantic_only=True, default="sam")

# ormar >= 0.20
class DishV20(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
        tablename="dishes_v20"
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    cook: str = "sam"  # this is normal pydantic field
```

## `property_field` decorator is no longer supported

`property_field` decorator was used to provide a way to pass calculated fields that were included in dictionary/ serialized json representation of the model.
Version 2.X of pydantic introduced such a possibility, so you should now switch to the one native to the pydantic.

```python
import databases
import ormar
import sqlalchemy
import pydantic

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()

# ormar < 0.20
class Employee(ormar.Model):
    class Meta:
        database = database
        metadata = metadata
    

    id: int = ormar.Integer(primary_key=True)
    first_name: str = ormar.String(max_length=100)
    last_name: str = ormar.String(max_length=100)
    
    @ormar.property_field()
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

# ormar >= 0.20
class EmployeeV20(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
    )

    id: int = ormar.Integer(primary_key=True)
    first_name: str = ormar.String(max_length=100)
    last_name: str = ormar.String(max_length=100)

    @pydantic.computed_field()
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
```

## Deprecated methods

All methods listed below are deprecated and will be removed in version 0.30 of `ormar`.

### `dict()` becomes the `model_dump()`

```python
import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()

class Album(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
        tablename="albums"
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    favorite: bool = ormar.Boolean(default=False)

album = Album(name="Dark Side of the Moon")
    
# ormar < 0.20
album_dict = album.dict()

# ormar >= 0.20
new_album_dict = album.model_dump() 
```

Note that parameters remain the same i.e. `include`, `exclude` etc.

### `json()` becomes the `model_dump_json()`

```python
import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()

class Album(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
        tablename="albums"
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    favorite: bool = ormar.Boolean(default=False)

album = Album(name="Dark Side of the Moon")
    
# ormar < 0.20
album_json= album.json()

# ormar >= 0.20
new_album_dict = album.model_dump_json() 
```

Note that parameters remain the same i.e. `include`, `exclude` etc.

### `construct()` becomes the `model_construct()`

```python
import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()

class Album(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database,
        metadata=metadata,
        tablename="albums"
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    favorite: bool = ormar.Boolean(default=False)
    
params = {
    "name": "Dark Side of the Moon",
    "favorite": True,
}
# ormar < 0.20
album = Album.construct(**params)

# ormar >= 0.20
album = Album.model_construct(**params)
```

To read more about construct please refer to `pydantic` documentation.