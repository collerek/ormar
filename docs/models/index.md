# Models

## Defining models

By defining an ormar Model you get corresponding **Pydantic model** as well as **Sqlalchemy table** for free.
They are being managed in the background and you do not have to create them on your own.

### Model Class

To build an ormar model you simply need to inherit a `ormar.Model` class.

```Python hl_lines="10"
--8<-- "../docs_src/models/docs001.py"
```

### Defining Fields

Next assign one or more of the [Fields][fields] as a class level variables.

#### Basic Field Types

Each table **has to** have a primary key column, which you specify by setting `primary_key=True` on selected field.

Only one primary key column is allowed.

```Python hl_lines="15 16 17"
--8<-- "../docs_src/models/docs001.py"
```

!!! warning 
    Not assigning `primary_key` column or assigning more than one column per `Model` will raise `ModelDefinitionError`
    exception.

By default if you assign primary key to `Integer` field, the `autoincrement` option is set to true.

You can disable by passing `autoincrement=False`.

```Python 
id: int = ormar.Integer(primary_key=True, autoincrement=False)
```

#### Non Database Fields

Note that if you need a normal pydantic field in your model (used to store value on model or pass around some value) you can define a 
field with parameter `pydantic_only=True`.

Fields created like this are added to the `pydantic` model fields -> so are subject to validation according to `Field` type, 
also appear in `dict()` and `json()` result. 

The difference is that **those fields are not saved in the database**. So they won't be included in underlying sqlalchemy `columns`, 
or `table` variables (check [Internals][Internals] section below to see how you can access those if you need).

Subsequently `pydantic_only` fields won't be included in migrations or any database operation (like `save`, `update` etc.)

Fields like those can be passed around into payload in `fastapi` request and will be returned in `fastapi` response 
(of course only if you set their value somewhere in your code as the value is **not** fetched from the db. 
If you pass a value in `fastapi` `request` and return the same instance that `fastapi` constructs for you in `request_model`
you should get back exactly same value in `response`.).

!!!warning
    `pydantic_only=True` fields are always **Optional** and it cannot be changed (otherwise db load validation would fail)

!!!tip
    `pydantic_only=True` fields are a good solution if you need to pass additional information from outside of your API 
    (i.e. frontend). They are not stored in db but you can access them in your `APIRoute` code and they also have `pydantic` validation. 

```Python hl_lines="18"
--8<-- "../docs_src/models/docs014.py"
```

If you combine `pydantic_only=True` field with `default` parameter and do not pass actual value in request you will always get default value.
Since it can be a function you can set `default=datetime.datetime.now` and get current timestamp each time you call an endpoint etc.

!!!note
    Note that both `pydantic_only` and `property_field` decorated field can be included/excluded in both `dict()` and `fastapi`
    response with `include`/`exclude` and `response_model_include`/`response_model_exclude` accordingly.

```python
# <==related of code removed for clarity==>
class User(ormar.Model):
    class Meta:
        tablename: str = "users2"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    email: str = ormar.String(max_length=255, nullable=False)
    password: str = ormar.String(max_length=255)
    first_name: str = ormar.String(max_length=255)
    last_name: str = ormar.String(max_length=255)
    category: str = ormar.String(max_length=255, nullable=True)
    timestamp: datetime.datetime = ormar.DateTime(
        pydantic_only=True, default=datetime.datetime.now
    )

# <==related of code removed for clarity==>
app =FastAPI()

@app.post("/users/")
async def create_user(user: User):
    return await user.save()

# <==related of code removed for clarity==>

def test_excluding_fields_in_endpoints():
    client = TestClient(app)
    with client as client:
        timestamp = datetime.datetime.now()

        user = {
            "email": "test@domain.com",
            "password": "^*^%A*DA*IAAA",
            "first_name": "John",
            "last_name": "Doe",
            "timestamp": str(timestamp),
        }
        response = client.post("/users/", json=user)
        assert list(response.json().keys()) == [
            "id",
            "email",
            "first_name",
            "last_name",
            "category",
            "timestamp",
        ]
        # returned is the same timestamp
        assert response.json().get("timestamp") == str(timestamp).replace(" ", "T")


# <==related of code removed for clarity==>
```

#### Property fields

Sometimes it's desirable to do some kind of calculation on the model instance. One of the most common examples can be concatenating
two or more fields. Imagine you have `first_name` and `last_name` fields on your model, but would like to have `full_name` in the result
of the `fastapi` query. 

You can create a new `pydantic` model with a `method` that accepts only `self` (so like default python `@property`) 
and populate it in your code. 

But it's so common that `ormar` has you covered. You can "materialize" a `property_field` on you `Model`.   

!!!warning
    `property_field` fields are always **Optional** and it cannot be changed (otherwise db load validation would fail)

```Python hl_lines="20-22"
--8<-- "../docs_src/models/docs015.py"
```

!!!warning
    The decorated function has to accept only one parameter, and that parameter have to be `self`. 
    
    If you try to decorate a function with more parameters `ormar` will raise `ModelDefinitionError`.
    
    Sample:
    
    ```python
    # will raise ModelDefinitionError
    @property_field
    def prefixed_name(self, prefix="prefix_"):
        return 'custom_prefix__' + self.name
    
    # will raise ModelDefinitionError 
    # (calling first param something else than 'self' is a bad practice anyway)
    @property_field
    def prefixed_name(instance):
        return 'custom_prefix__' + self.name
    ```
    
Note that `property_field` decorated methods do not go through verification (but that might change in future) and are only available
in the response from `fastapi` and `dict()` and `json()` methods. You cannot pass a value for this field in the request 
(or rather you can but it will be discarded by ormar so really no point but no Exception will be raised).

!!!note
    Note that both `pydantic_only` and `property_field` decorated field can be included/excluded in both `dict()` and `fastapi`
    response with `include`/`exclude` and `response_model_include`/`response_model_exclude` accordingly.
    
!!!tip
    Note that `@property_field` decorator is designed to replace the python `@property` decorator, you do not have to combine them.
    
    In theory you can cause `ormar` have a failsafe mechanism, but note that i.e. `mypy` will complain about re-decorating a property.
    
    ```python
    # valid and working but unnecessary and mypy will complain
    @property_field
    @property
    def prefixed_name(self):
        return 'custom_prefix__' + self.name
    ```
    
```python
# <==related of code removed for clarity==>
def gen_pass():  # note: NOT production ready 
    choices = string.ascii_letters + string.digits + "!@#$%^&*()"
    return "".join(random.choice(choices) for _ in range(20))

class RandomModel(ormar.Model):
    class Meta:
        tablename: str = "random_users"
        metadata = metadata
        database = database

        include_props_in_dict = True

    id: int = ormar.Integer(primary_key=True)
    password: str = ormar.String(max_length=255, default=gen_pass)
    first_name: str = ormar.String(max_length=255, default="John")
    last_name: str = ormar.String(max_length=255)
    created_date: datetime.datetime = ormar.DateTime(
        server_default=sqlalchemy.func.now()
    )

    @property_field
    def full_name(self) -> str:
        return " ".join([self.first_name, self.last_name])

# <==related of code removed for clarity==>
app =FastAPI()

# explicitly exclude property_field in this endpoint
@app.post("/random/", response_model=RandomModel, response_model_exclude={"full_name"})
async def create_user(user: RandomModel):
    return await user.save()

# <==related of code removed for clarity==>

def test_excluding_property_field_in_endpoints2():
    client = TestClient(app)
    with client as client:
        RandomModel.Meta.include_props_in_dict = True
        user3 = {"last_name": "Test"}
        response = client.post("/random3/", json=user3)
        assert list(response.json().keys()) == [
            "id",
            "password",
            "first_name",
            "last_name",
            "created_date",
        ]
        # despite being decorated with property_field if you explictly exclude it it will be gone
        assert response.json().get("full_name") is None

# <==related of code removed for clarity==>
```

#### Fields names vs Column names

By default names of the fields will be used for both the underlying `pydantic` model and `sqlalchemy` table.

If for whatever reason you prefer to change the name in the database but keep the name in the model you can do this 
with specifying `name` parameter during Field declaration

Here you have a sample model with changed names
```Python hl_lines="16-19"
--8<-- "../docs_src/models/docs008.py"
```

Note that you can also change the ForeignKey column name
```Python hl_lines="21"
--8<-- "../docs_src/models/docs009.py"
```

But for now you cannot change the ManyToMany column names as they go through other Model anyway.
```Python hl_lines="28"
--8<-- "../docs_src/models/docs010.py"
```

### Type Hints & Legacy

Before version 0.4.0 `ormar` supported only one way of defining `Fields` on a `Model` using python type hints as pydantic.

```Python hl_lines="15-17"
--8<-- "../docs_src/models/docs011.py"
```

But that didn't play well with static type checkers like `mypy` and `pydantic` PyCharm plugin.

Therefore from version >=0.4.0 `ormar` switched to new notation.

```Python hl_lines="15-17"
--8<-- "../docs_src/models/docs001.py"
```

Note that type hints are **optional** so perfectly valid `ormar` code can look like this:

```Python hl_lines="15-17"
--8<-- "../docs_src/models/docs012.py"
```

!!!warning
    Even if you use type hints **`ormar` does not use them to construct `pydantic` fields!**
    
    Type hints are there only to support static checkers and linting, 
    `ormar` construct annotations used by `pydantic` from own fields.



### Dependencies

Since ormar depends on [`databases`][databases] and [`sqlalchemy-core`][sqlalchemy-core] for database connection 
and table creation you need to assign each `Model` with two special parameters.

#### Databases

One is `Database` instance created with your database url in [sqlalchemy connection string][sqlalchemy connection string] format.

Created instance needs to be passed to every `Model` with `Meta` class `database` parameter.

```Python hl_lines="1 6 12"
--8<-- "../docs_src/models/docs001.py"
```

!!! tip
    You need to create the `Database` instance **only once** and use it for all models. 
    You can create several ones if you want to use multiple databases.

#### Sqlalchemy

Second dependency is sqlalchemy `MetaData` instance.

Created instance needs to be passed to every `Model` with `Meta` class `metadata` parameter.

```Python hl_lines="2 7 13"
--8<-- "../docs_src/models/docs001.py"
```

!!! tip
    You need to create the `MetaData` instance **only once** and use it for all models. 
    You can create several ones if you want to use multiple databases.

#### Best practice

Only thing that `ormar` expects is a class with name `Meta` and two class variables: `metadata` and `databases`.

So instead of providing the same parameters over and over again for all models you should creata a class and subclass it in all models.

```Python hl_lines="14 20 33"
--8<-- "../docs_src/models/docs013.py"
```

!!!warning
    You need to subclass your `MainMeta` class in each `Model` class as those classes store configuration variables 
    that otherwise would be overwritten by each `Model`.

### Table Names

By default table name is created from Model class name as lowercase name plus 's'.

You can overwrite this parameter by providing `Meta` class `tablename` argument.

```Python hl_lines="12 13 14"
--8<-- "../docs_src/models/docs002.py"
```

### Constraints

On a model level you can also set model-wise constraints on sql columns.

Right now only `UniqueColumns` constraint is present. 

!!!tip
    To read more about columns constraints like `primary_key`, `unique`, `ForeignKey` etc. visit [fields][fields].

You can set this parameter by providing `Meta` class `constraints` argument.

```Python hl_lines="14-17"
--8<-- "../docs_src/models/docs006.py"
```

!!!note
        Note that constraints are meant for combination of columns that should be unique. 
        To set one column as unique use [`unique`](../fields/common-parameters.md#unique) common parameter. 
        Of course you can set many columns as unique with this param but each of them will be checked separately.

### Pydantic configuration

As each `ormar.Model` is also a `pydantic` model, you might want to tweak the settings of the pydantic configuration.

The way to do this in pydantic is to adjust the settings on the `Config` class provided to your model, and it works exactly the same for ormer.Models.

So in order to set your own preferences you need to provide not only the `Meta` class but also the `Config` class to your model.

!!!note
        To read more about available settings visit the [pydantic](https://pydantic-docs.helpmanual.io/usage/model_config/) config page.

Note that if you do not provide your own configuration, ormar will do it for you.
The default config provided is as follows:

```python
class Config(pydantic.BaseConfig):
    orm_mode = True
    validate_assignment = True
```

So to overwrite setting or provide your own a sample model can look like following:
```Python hl_lines="15-16"
--8<-- "../docs_src/models/docs016.py"
```

## Model sort order

When querying the database with given model by default the Model is ordered by the `primary_key`
column ascending. If you wish to change the default behaviour you can do it by providing `orders_by`
parameter to model `Meta` class.

Sample default ordering:
```python
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database

# default sort by column id ascending
class Author(ormar.Model):
    class Meta(BaseMeta):
        tablename = "authors"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
```
Modified
```python

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database

# now default sort by name descending
class Author(ormar.Model):
    class Meta(BaseMeta):
        tablename = "authors"
        orders_by = ["-name"]

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
```

## Model Initialization

There are two ways to create and persist the `Model` instance in the database.

!!!tip 
    Use `ipython` to try this from the console, since it supports `await`.

If you plan to modify the instance in the later execution of your program you can initiate your `Model` as a normal class and later await a `save()` call.  

```Python hl_lines="20 21"
--8<-- "../docs_src/models/docs007.py"
```

If you want to initiate your `Model` and at the same time save in in the database use a QuerySet's method `create()`.

For creating multiple objects at once a `bulk_create()` QuerySet's method is available.

Each model has a `QuerySet` initialised as `objects` parameter 

```Python hl_lines="23"
--8<-- "../docs_src/models/docs007.py"
```

!!!info
    To read more about `QuerySets` (including bulk operations) and available methods visit [queries][queries]

## `Model` save status

Each model instance is a separate python object and they do not know anything about each other.

```python
track1 = await Track.objects.get(name='The Bird')
track2 = await Track.objects.get(name='The Bird')
assert track1 == track2 # True

track1.name = 'The Bird2'
await track1.save()
assert track1.name == track2.name # False
# track2 does not update and knows nothing about track1
```

The objects itself have a saved status, which is set as following:

*  Model is saved after `save/update/load/upsert` method on model
*  Model is saved after `create/get/first/all/get_or_create/update_or_create` method
*  Model is saved when passed to `bulk_update` and `bulk_create`
*  Model is saved after `adding/removing` `ManyToMany` related objects (through model instance auto saved/deleted)
*  Model is **not** saved after change of any own field (including `pk` as `Model.pk` alias)
*  Model is **not** saved after adding/removing `ForeignKey` related object (fk column not saved)
*  Model is **not** saved after instantiation with `__init__` (w/o `QuerySet.create` or before calling `save`)

You can check if model is saved with `ModelInstance.saved` property

[fields]: ../fields/field-types.md
[relations]: ../relations/index.md
[queries]: ../queries/index.md
[pydantic]: https://pydantic-docs.helpmanual.io/
[sqlalchemy-core]: https://docs.sqlalchemy.org/en/latest/core/
[sqlalchemy-metadata]: https://docs.sqlalchemy.org/en/13/core/metadata.html
[databases]: https://github.com/encode/databases
[sqlalchemy connection string]: https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls
[sqlalchemy table creation]: https://docs.sqlalchemy.org/en/13/core/metadata.html#creating-and-dropping-database-tables
[alembic]: https://alembic.sqlalchemy.org/en/latest/tutorial.html
[save status]:  ../models/index/#model-save-status
[Internals]:  ../models/internals.md