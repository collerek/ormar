<a name="models.model"></a>
# models.model

<a name="models.model.Model"></a>
## Model Objects

```python
class Model(NewBaseModel)
```

<a name="models.model.Model.from_row"></a>
#### from\_row

```python
 | @classmethod
 | from_row(cls: Type[T], row: sqlalchemy.engine.ResultProxy, select_related: List = None, related_models: Any = None, previous_model: Type[T] = None, source_model: Type[T] = None, related_name: str = None, fields: Optional[Union[Dict, Set]] = None, exclude_fields: Optional[Union[Dict, Set]] = None, current_relation_str: str = None) -> Optional[T]
```

Model method to convert raw sql row from database into ormar.Model instance.
Traverses nested models if they were specified in select_related for query.

Called recurrently and returns model instance if it's present in the row.
Note that it's processing one row at a time, so if there are duplicates of
parent row that needs to be joined/combined
(like parent row in sql join with 2+ child rows)
instances populated in this method are later combined in the QuerySet.
Other method working directly on raw database results is in prefetch_query,
where rows are populated in a different way as they do not have
nested models in result.

**Arguments**:

- `row (sqlalchemy.engine.result.ResultProxy)`: raw result row from the database
- `select_related (List)`: list of names of related models fetched from database
- `related_models (Union[List, Dict])`: list or dict of related models
- `previous_model (Model class)`: internal param for nested models to specify table_prefix
- `related_name (str)`: internal parameter - name of current nested model
- `fields (Optional[Union[Dict, Set]])`: fields and related model fields to include
if provided only those are included
- `exclude_fields (Optional[Union[Dict, Set]])`: fields and related model fields to exclude
excludes the fields even if they are provided in fields

**Returns**:

`(Optional[Model])`: returns model if model is populated from database

<a name="models.model.Model.populate_nested_models_from_row"></a>
#### populate\_nested\_models\_from\_row

```python
 | @classmethod
 | populate_nested_models_from_row(cls, item: dict, row: sqlalchemy.engine.ResultProxy, related_models: Any, fields: Optional[Union[Dict, Set]] = None, exclude_fields: Optional[Union[Dict, Set]] = None, current_relation_str: str = None, source_model: Type[T] = None) -> dict
```

Traverses structure of related models and populates the nested models
from the database row.
Related models can be a list if only directly related models are to be
populated, converted to dict if related models also have their own related
models to be populated.

Recurrently calls from_row method on nested instances and create nested
instances. In the end those instances are added to the final model dictionary.

**Arguments**:

- `source_model (Type[Model])`: source model from which relation started
- `current_relation_str (str)`: joined related parts into one string
- `item (Dict)`: dictionary of already populated nested models, otherwise empty dict
- `row (sqlalchemy.engine.result.ResultProxy)`: raw result row from the database
- `related_models (Union[Dict, List])`: list or dict of related models
- `fields (Optional[Union[Dict, Set]])`: fields and related model fields to include -
if provided only those are included
- `exclude_fields (Optional[Union[Dict, Set]])`: fields and related model fields to exclude
excludes the fields even if they are provided in fields

**Returns**:

`(Dict)`: dictionary with keys corresponding to model fields names
and values are database values

<a name="models.model.Model.extract_prefixed_table_columns"></a>
#### extract\_prefixed\_table\_columns

```python
 | @classmethod
 | extract_prefixed_table_columns(cls, item: dict, row: sqlalchemy.engine.result.ResultProxy, table_prefix: str, fields: Optional[Union[Dict, Set]] = None, exclude_fields: Optional[Union[Dict, Set]] = None) -> dict
```

Extracts own fields from raw sql result, using a given prefix.
Prefix changes depending on the table's position in a join.

If the table is a main table, there is no prefix.
All joined tables have prefixes to allow duplicate column names,
as well as duplicated joins to the same table from multiple different tables.

Extracted fields populates the related dict later used to construct a Model.

Used in Model.from_row and PrefetchQuery._populate_rows methods.

**Arguments**:

- `item (Dict)`: dictionary of already populated nested models, otherwise empty dict
- `row (sqlalchemy.engine.result.ResultProxy)`: raw result row from the database
- `table_prefix (str)`: prefix of the table from AliasManager
each pair of tables have own prefix (two of them depending on direction) -
used in joins to allow multiple joins to the same table.
- `fields (Optional[Union[Dict, Set]])`: fields and related model fields to include -
if provided only those are included
- `exclude_fields (Optional[Union[Dict, Set]])`: fields and related model fields to exclude
excludes the fields even if they are provided in fields

**Returns**:

`(Dict)`: dictionary with keys corresponding to model fields names
and values are database values

<a name="models.model.Model.upsert"></a>
#### upsert

```python
 | async upsert(**kwargs: Any) -> T
```

Performs either a save or an update depending on the presence of the pk.
If the pk field is filled it's an update, otherwise the save is performed.
For save kwargs are ignored, used only in update if provided.

**Arguments**:

- `kwargs (Any)`: list of fields to update

**Returns**:

`(Model)`: saved Model

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

`(Model)`: saved Model

<a name="models.model.Model.save_related"></a>
#### save\_related

```python
 | async save_related(follow: bool = False, visited: Set = None, update_count: int = 0) -> int
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

- `follow (bool)`: flag to trigger deep save -
by default only directly related models are saved
with follow=True also related models of related models are saved
- `visited (Set)`: internal parameter for recursive calls - already visited models
- `update_count (int)`: internal parameter for recursive calls -
number of updated instances

**Returns**:

`(int)`: number of updated/saved models

<a name="models.model.Model._update_and_follow"></a>
#### \_update\_and\_follow

```python
 | @staticmethod
 | async _update_and_follow(rel: T, follow: bool, visited: Set, update_count: int) -> Tuple[int, Set]
```

Internal method used in save_related to follow related models and update numbers
of updated related instances.

**Arguments**:

- `rel (Model)`: Model to follow
- `follow (bool)`: flag to trigger deep save -
by default only directly related models are saved
with follow=True also related models of related models are saved
- `visited (Set)`: internal parameter for recursive calls - already visited models
- `update_count (int)`: internal parameter for recursive calls -
number of updated instances

**Returns**:

`(Tuple[int, Set])`: tuple of update count and visited

<a name="models.model.Model.update"></a>
#### update

```python
 | async update(**kwargs: Any) -> T
```

Performs update of Model instance in the database.
Fields can be updated before or you can pass them as kwargs.

Sends pre_update and post_update signals.

Sets model save status to True.

**Raises**:

- `ModelPersistenceError`: If the pk column is not set

**Arguments**:

- `kwargs (Any)`: list of fields to update as field=value pairs

**Returns**:

`(Model)`: updated Model

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

`(int)`: number of deleted rows (for some backends)

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

`(Model)`: reloaded Model

