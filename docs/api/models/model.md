<a name="models.model"></a>
# models.model

<a name="models.model.Model"></a>
## Model Objects

```python
class Model(ModelRow)
```

<a name="models.model.Model.upsert"></a>
#### upsert

```python
 | async upsert(**kwargs: Any) -> T
```

Performs either a save or an update depending on the presence of the pk.
If the pk field is filled it's an update, otherwise the save is performed.
For save kwargs are ignored, used only in update if provided.

**Arguments**:

- `kwargs` (`Any`): list of fields to update

**Returns**:

`Model`: saved Model

<a name="models.model.Model.save"></a>
#### save

```python
 | async save() -> T
```

Performs a save of given Model instance.
If primary key is already saved, db backend will throw integrity error.

Related models are saved by pk number, reverse relation and many to many fields
are not saved - use corresponding relations methods.

If there are fields with server_default set and those fields
are not already filled save will trigger also a second query
to refreshed the fields populated server side.

Does not recognize if model was previously saved.
If you want to perform update or insert depending on the pk
fields presence use upsert.

Sends pre_save and post_save signals.

Sets model save status to True.

**Returns**:

`Model`: saved Model

<a name="models.model.Model.save_related"></a>
#### save\_related

```python
 | async save_related(follow: bool = False, save_all: bool = False, relation_map: Dict = None, exclude: Union[Set, Dict] = None, update_count: int = 0, previous_model: "Model" = None, relation_field: Optional["ForeignKeyField"] = None) -> int
```

Triggers a upsert method on all related models
if the instances are not already saved.
By default saves only the directly related ones.

If follow=True is set it saves also related models of related models.

To not get stuck in an infinite loop as related models also keep a relation
to parent model visited models set is kept.

That way already visited models that are nested are saved, but the save do not
follow them inside. So Model A -> Model B -> Model A -> Model C will save second
Model A but will never follow into Model C.
Nested relations of those kind need to be persisted manually.

**Arguments**:

by default only directly related models are saved
with follow=True also related models of related models are saved
number of updated instances
- `relation_field` (`Optional[ForeignKeyField]`): field with relation leading to this model
- `previous_model` (`Model`): previous model from which method came
- `exclude` (`Union[Set, Dict]`): items to exclude during saving of relations
- `relation_map` (`Dict`): map of relations to follow
- `save_all` (`bool`): flag if all models should be saved or only not saved ones
- `follow` (`bool`): flag to trigger deep save -
- `update_count` (`int`): internal parameter for recursive calls -

**Returns**:

`int`: number of updated/saved models

<a name="models.model.Model.update"></a>
#### update

```python
 | async update(_columns: List[str] = None, **kwargs: Any) -> T
```

Performs update of Model instance in the database.
Fields can be updated before or you can pass them as kwargs.

Sends pre_update and post_update signals.

Sets model save status to True.

**Arguments**:

- `_columns` (`List`): list of columns to update, if None all are updated
- `kwargs` (`Any`): list of fields to update as field=value pairs

**Raises**:

- `ModelPersistenceError`: If the pk column is not set

**Returns**:

`Model`: updated Model

<a name="models.model.Model.delete"></a>
#### delete

```python
 | async delete() -> int
```

Removes the Model instance from the database.

Sends pre_delete and post_delete signals.

Sets model save status to False.

Note it does not delete the Model itself (python object).
So you can delete and later save (since pk is deleted no conflict will arise)
or update and the Model will be saved in database again.

**Returns**:

`int`: number of deleted rows (for some backends)

<a name="models.model.Model.load"></a>
#### load

```python
 | async load() -> T
```

Allow to refresh existing Models fields from database.
Be careful as the related models can be overwritten by pk_only models in load.
Does NOT refresh the related models fields if they were loaded before.

**Raises**:

- `NoMatch`: If given pk is not found in database.

**Returns**:

`Model`: reloaded Model

<a name="models.model.Model.load_all"></a>
#### load\_all

```python
 | async load_all(follow: bool = False, exclude: Union[List, str, Set, Dict] = None, order_by: Union[List, str] = None) -> T
```

Allow to refresh existing Models fields from database.
Performs refresh of the related models fields.

By default loads only self and the directly related ones.

If follow=True is set it loads also related models of related models.

To not get stuck in an infinite loop as related models also keep a relation
to parent model visited models set is kept.

That way already visited models that are nested are loaded, but the load do not
follow them inside. So Model A -> Model B -> Model C -> Model A -> Model X
will load second Model A but will never follow into Model X.
Nested relations of those kind need to be loaded manually.

**Arguments**:

by default only directly related models are saved
with follow=True also related models of related models are saved
- `order_by` (`Union[List, str]`): columns by which models should be sorted
- `exclude` (`Union[List, str, Set, Dict]`): related models to exclude
- `follow` (`bool`): flag to trigger deep save -

**Raises**:

- `NoMatch`: If given pk is not found in database.

**Returns**:

`Model`: reloaded Model

