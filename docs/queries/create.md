# Create / Insert data into database

* `create(**kwargs): -> Model`
* `get_or_create(**kwargs) -> Model`
* `update_or_create(**kwargs) -> Model`
* `bulk_create(objects: List[Model]) -> None`
* `Model.save()` method
* `Model.upsert()` method

## create

`create(**kwargs): -> Model`

Creates the model instance, saves it in a database and returns the updates model
(with pk populated if not passed and autoincrement is set).

The allowed kwargs are `Model` fields names and proper value types.

```python
malibu = await Album.objects.create(name="Malibu")
await Track.objects.create(album=malibu, title="The Bird", position=1)
```

The alternative is a split creation and persistence of the `Model`.

```python
malibu = Album(name="Malibu")
await malibu.save()
```

!!!tip Check other `Model` methods in [models][models]

## get_or_create

`get_or_create(**kwargs) -> Model`

Combination of create and get methods.

Tries to get a row meeting the criteria and if `NoMatch` exception is raised it creates
a new one with given kwargs.

```python
album = await Album.objects.get_or_create(name='The Cat')
# object is created as it does not exist
album2 = await Album.objects.get_or_create(name='The Cat')
assert album == album2
# return True as the same db row is returned
```

!!!warning Despite being a equivalent row from database the `album` and `album2` in
example above are 2 different python objects!
Updating one of them will not refresh the second one until you excplicitly load() the
fresh data from db.

!!!note Note that if you want to create a new object you either have to pass pk column
value or pk column has to be set as autoincrement

## update_or_create

`update_or_create(**kwargs) -> Model`

Updates the model, or in case there is no match in database creates a new one.

```Python hl_lines="26-32"
--8<-- "../docs_src/queries/docs003.py"
```

!!!note Note that if you want to create a new object you either have to pass pk column
value or pk column has to be set as autoincrement

## bulk_create

`bulk_create(objects: List["Model"]) -> None`

Allows you to create multiple objects at once.

A valid list of `Model` objects needs to be passed.

```python hl_lines="21-27"
--8<-- "../docs_src/queries/docs004.py"
```

## Model method