# Selecting subset of columns

*  `fields(columns: Union[List, str, set, dict]) -> QuerySet`
*  `exclude_fields(columns: Union[List, str, set, dict]) -> QuerySet`

## fields

`fields(columns: Union[List, str, set, dict]) -> QuerySet`

With `fields()` you can select subset of model columns to limit the data load.

!!!note Note that `fields()` and `exclude_fields()` works both for main models (on
normal queries like `get`, `all` etc.)
as well as `select_related` and `prefetch_related` models (with nested notation).

Given a sample data like following:

```python
--8 < -- "../docs_src/queries/docs006.py"
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

!!!warning Mandatory fields cannot be excluded as it will raise `ValidationError`, to
exclude a field it has to be nullable.

You cannot exclude mandatory model columns - `manufacturer__name` in this example.

```python
await Car.objects.select_related('manufacturer').fields(
    ['id', 'name', 'manufacturer__founded']).all()
# will raise pydantic ValidationError as company.name is required
```

!!!tip Pk column cannot be excluded - it's always auto added even if not explicitly
included.

You can also pass fields to include as dictionary or set.

To mark a field as included in a dictionary use it's name as key and ellipsis as value.

To traverse nested models use nested dictionaries.

To include fields at last level instead of nested dictionary a set can be used.

To include whole nested model specify model related field name and ellipsis.

Below you can see examples that are equivalent:

```python
--8 < -- "../docs_src/queries/docs009.py"
```

!!!note All methods that do not return the rows explicitly returns a QueySet instance so
you can chain them together

    So operations like `filter()`, `select_related()`, `limit()` and `offset()` etc. can be chained.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`

## exclude_fields

`exclude_fields(columns: Union[List, str, set, dict]) -> QuerySet`

With `exclude_fields()` you can select subset of model columns that will be excluded to
limit the data load.

It's the opposite of `fields()` method so check documentation above to see what options
are available.

Especially check above how you can pass also nested dictionaries and sets as a mask to
exclude fields from whole hierarchy.

!!!note Note that `fields()` and `exclude_fields()` works both for main models (on
normal queries like `get`, `all` etc.)
as well as `select_related` and `prefetch_related` models (with nested notation).

Below you can find few simple examples:

```python hl_lines="47 48 60 61 67"
--8<-- "../docs_src/queries/docs008.py"
```

!!!warning Mandatory fields cannot be excluded as it will raise `ValidationError`, to
exclude a field it has to be nullable.

!!!tip Pk column cannot be excluded - it's always auto added even if explicitly
excluded.

!!!note All methods that do not return the rows explicitly returns a QueySet instance so
you can chain them together

    So operations like `filter()`, `select_related()`, `limit()` and `offset()` etc. can be chained.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`
