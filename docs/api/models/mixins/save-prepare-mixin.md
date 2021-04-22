<a name="models.mixins.save_mixin"></a>
# models.mixins.save\_mixin

<a name="models.mixins.save_mixin.SavePrepareMixin"></a>
## SavePrepareMixin Objects

```python
class SavePrepareMixin(RelationMixin,  AliasMixin)
```

Used to prepare models to be saved in database

<a name="models.mixins.save_mixin.SavePrepareMixin.prepare_model_to_save"></a>
#### prepare\_model\_to\_save

```python
 | @classmethod
 | prepare_model_to_save(cls, new_kwargs: dict) -> dict
```

Combines all preparation methods before saving.
Removes primary key for if it's nullable or autoincrement pk field,
and it's set to None.
Substitute related models with their primary key values as fk column.
Populates the default values for field with default set and no value.
Translate columns into aliases (db names).

**Arguments**:

- `new_kwargs (Dict[str, str])`: dictionary of model that is about to be saved

**Returns**:

`(Dict[str, str])`: dictionary of model that is about to be saved

<a name="models.mixins.save_mixin.SavePrepareMixin._remove_not_ormar_fields"></a>
#### \_remove\_not\_ormar\_fields

```python
 | @classmethod
 | _remove_not_ormar_fields(cls, new_kwargs: dict) -> dict
```

Removes primary key for if it's nullable or autoincrement pk field,
and it's set to None.

**Arguments**:

- `new_kwargs (Dict[str, str])`: dictionary of model that is about to be saved

**Returns**:

`(Dict[str, str])`: dictionary of model that is about to be saved

<a name="models.mixins.save_mixin.SavePrepareMixin._remove_pk_from_kwargs"></a>
#### \_remove\_pk\_from\_kwargs

```python
 | @classmethod
 | _remove_pk_from_kwargs(cls, new_kwargs: dict) -> dict
```

Removes primary key for if it's nullable or autoincrement pk field,
and it's set to None.

**Arguments**:

- `new_kwargs (Dict[str, str])`: dictionary of model that is about to be saved

**Returns**:

`(Dict[str, str])`: dictionary of model that is about to be saved

<a name="models.mixins.save_mixin.SavePrepareMixin.parse_non_db_fields"></a>
#### parse\_non\_db\_fields

```python
 | @classmethod
 | parse_non_db_fields(cls, model_dict: Dict) -> Dict
```

Receives dictionary of model that is about to be saved and changes uuid fields
to strings in bulk_update.

**Arguments**:

- `model_dict (Dict)`: dictionary of model that is about to be saved

**Returns**:

`(Dict)`: dictionary of model that is about to be saved

<a name="models.mixins.save_mixin.SavePrepareMixin.substitute_models_with_pks"></a>
#### substitute\_models\_with\_pks

```python
 | @classmethod
 | substitute_models_with_pks(cls, model_dict: Dict) -> Dict
```

Receives dictionary of model that is about to be saved and changes all related
models that are stored as foreign keys to their fk value.

**Arguments**:

- `model_dict (Dict)`: dictionary of model that is about to be saved

**Returns**:

`(Dict)`: dictionary of model that is about to be saved

<a name="models.mixins.save_mixin.SavePrepareMixin.populate_default_values"></a>
#### populate\_default\_values

```python
 | @classmethod
 | populate_default_values(cls, new_kwargs: Dict) -> Dict
```

Receives dictionary of model that is about to be saved and populates the default
value on the fields that have the default value set, but no actual value was
passed by the user.

**Arguments**:

- `new_kwargs (Dict)`: dictionary of model that is about to be saved

**Returns**:

`(Dict)`: dictionary of model that is about to be saved

<a name="models.mixins.save_mixin.SavePrepareMixin.validate_choices"></a>
#### validate\_choices

```python
 | @classmethod
 | validate_choices(cls, new_kwargs: Dict) -> Dict
```

Receives dictionary of model that is about to be saved and validates the
fields with choices set to see if the value is allowed.

**Arguments**:

- `new_kwargs (Dict)`: dictionary of model that is about to be saved

**Returns**:

`(Dict)`: dictionary of model that is about to be saved

<a name="models.mixins.save_mixin.SavePrepareMixin._upsert_model"></a>
#### \_upsert\_model

```python
 | @staticmethod
 | async _upsert_model(instance: "Model", save_all: bool, previous_model: Optional["Model"], relation_field: Optional["ForeignKeyField"], update_count: int) -> int
```

Method updates given instance if:

* instance is not saved or
* instance have no pk or
* save_all=True flag is set

and instance is not __pk_only__.

If relation leading to instance is a ManyToMany also the through model is saved

**Arguments**:

- `instance (Model)`: current model to upsert
- `save_all (bool)`: flag if all models should be saved or only not saved ones
- `relation_field (Optional[ForeignKeyField])`: field with relation
- `previous_model (Model)`: previous model from which method came
- `update_count (int)`: no of updated models

**Returns**:

`(int)`: no of updated models

<a name="models.mixins.save_mixin.SavePrepareMixin._upsert_through_model"></a>
#### \_upsert\_through\_model

```python
 | @staticmethod
 | async _upsert_through_model(instance: "Model", previous_model: "Model", relation_field: "ForeignKeyField") -> None
```

Upsert through model for m2m relation.

**Arguments**:

- `instance (Model)`: current model to upsert
- `relation_field (Optional[ForeignKeyField])`: field with relation
- `previous_model (Model)`: previous model from which method came

<a name="models.mixins.save_mixin.SavePrepareMixin._update_relation_list"></a>
#### \_update\_relation\_list

```python
 | async _update_relation_list(fields_list: Collection["ForeignKeyField"], follow: bool, save_all: bool, relation_map: Dict, update_count: int) -> int
```

Internal method used in save_related to follow deeper from
related models and update numbers of updated related instances.

**Arguments**:

- `fields_list (Collection["ForeignKeyField"])`: list of ormar fields to follow and save
- `relation_map (Dict)`: map of relations to follow
- `follow (bool)`: flag to trigger deep save -
by default only directly related models are saved
with follow=True also related models of related models are saved
- `update_count (int)`: internal parameter for recursive calls -
number of updated instances

**Returns**:

`(int)`: tuple of update count and visited

