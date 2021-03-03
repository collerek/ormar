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

