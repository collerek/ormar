<a name="models.helpers.models"></a>
# models.helpers.models

<a name="models.helpers.models.is_field_an_forward_ref"></a>
#### is\_field\_an\_forward\_ref

```python
is_field_an_forward_ref(field: "BaseField") -> bool
```

Checks if field is a relation field and whether any of the referenced models
are ForwardRefs that needs to be updated before proceeding.

**Arguments**:

- `field` (`Type[BaseField]`): model field to verify

**Returns**:

`bool`: result of the check

<a name="models.helpers.models.populate_default_options_values"></a>
#### populate\_default\_options\_values

```python
populate_default_options_values(new_model: Type["Model"], model_fields: Dict) -> None
```

Sets all optional Meta values to it's defaults
and set model_fields that were already previously extracted.

Here should live all options that are not overwritten/set for all models.

Current options are:
* constraints = []
* abstract = False

**Arguments**:

- `new_model` (`Model class`): newly constructed Model
- `model_fields` (`Union[Dict[str, type], Dict]`): dict of model fields

<a name="models.helpers.models.substitue_backend_pool_for_sqlite"></a>
#### substitue\_backend\_pool\_for\_sqlite

```python
substitue_backend_pool_for_sqlite(new_model: Type["Model"]) -> None
```

Recreates Connection pool for sqlite3 with new factory that
executes "PRAGMA foreign_keys=1; on initialization to enable foreign keys.

**Arguments**:

- `new_model` (`Model class`): newly declared ormar Model

<a name="models.helpers.models.check_required_meta_parameters"></a>
#### check\_required\_meta\_parameters

```python
check_required_meta_parameters(new_model: Type["Model"]) -> None
```

Verifies if ormar.Model has database and metadata set.

Recreates Connection pool for sqlite3

**Arguments**:

- `new_model` (`Model class`): newly declared ormar Model

<a name="models.helpers.models.extract_annotations_and_default_vals"></a>
#### extract\_annotations\_and\_default\_vals

```python
extract_annotations_and_default_vals(attrs: Dict) -> Tuple[Dict, Dict]
```

Extracts annotations from class namespace dict and triggers
extraction of ormar model_fields.

**Arguments**:

- `attrs` (`Dict`): namespace of the class created

**Returns**:

`Tuple[Dict, Dict]`: namespace of the class updated, dict of extracted model_fields

<a name="models.helpers.models.group_related_list"></a>
#### group\_related\_list

```python
group_related_list(list_: List) -> collections.OrderedDict
```

Translates the list of related strings into a dictionary.
That way nested models are grouped to traverse them in a right order
and to avoid repetition.

Sample: ["people__houses", "people__cars__models", "people__cars__colors"]
will become:
{'people': {'houses': [], 'cars': ['models', 'colors']}}

Result dictionary is sorted by length of the values and by key

**Arguments**:

- `list_` (`List[str]`): list of related models used in select related

**Returns**:

`Dict[str, List]`: list converted to dictionary to avoid repetition and group nested models

<a name="models.helpers.models.meta_field_not_set"></a>
#### meta\_field\_not\_set

```python
meta_field_not_set(model: Type["Model"], field_name: str) -> bool
```

Checks if field with given name is already present in model.Meta.
Then check if it's set to something truthful
(in practice meaning not None, as it's non or ormar Field only).

**Arguments**:

- `model` (`Model class`): newly constructed model
- `field_name` (`str`): name of the ormar field

**Returns**:

`bool`: result of the check

