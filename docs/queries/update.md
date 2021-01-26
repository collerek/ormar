# Update

*  `update(each: bool = False, **kwargs) -> int`
*  `update_or_create(**kwargs) -> Model`
*  `bulk_update(objects: List[Model], columns: List[str] = None) -> None`
*  `Model.update() method`
*  `Model.upsert() method`
*  `Model.save_related() method`

## update

`update(each: bool = False, **kwargs) -> int`

QuerySet level update is used to update multiple records with the same value at once.

You either have to filter the QuerySet first or provide a `each=True` flag to update
whole table.

If you do not provide this flag or a filter a `QueryDefinitionError` will be raised.

Return number of rows updated.

```Python hl_lines="26-28"
--8<-- "../docs_src/queries/docs002.py"
```

!!!warning Queryset needs to be filtered before updating to prevent accidental
overwrite.

    To update whole database table `each=True` needs to be provided as a safety switch

## update_or_create

`update_or_create(**kwargs) -> Model`

Updates the model, or in case there is no match in database creates a new one.

```Python hl_lines="26-32"
--8<-- "../docs_src/queries/docs003.py"
```

!!!note Note that if you want to create a new object you either have to pass pk column
value or pk column has to be set as autoincrement

## bulk_update

`bulk_update(objects: List["Model"], columns: List[str] = None) -> None`

Allows to update multiple instance at once.

All `Models` passed need to have primary key column populated.

You can also select which fields to update by passing `columns` list as a list of string
names.

```python hl_lines="8"
# continuing the example from bulk_create
# update objects
for todo in todoes:
    todo.completed = False

# perform update of all objects at once
# objects need to have pk column set, otherwise exception is raised
await ToDo.objects.bulk_update(todoes)

completed = await ToDo.objects.filter(completed=False).all()
assert len(completed) == 3
```

## Model method

