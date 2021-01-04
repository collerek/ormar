<a name="models.helpers.models"></a>
# models.helpers.models

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

- `new_model (Model class)`: newly constructed Model
- `model_fields (Union[Dict[str, type], Dict])`: 

<a name="models.helpers.models.extract_annotations_and_default_vals"></a>
#### extract\_annotations\_and\_default\_vals

```python
extract_annotations_and_default_vals(attrs: Dict) -> Tuple[Dict, Dict]
```

Extracts annotations from class namespace dict and triggers
extraction of ormar model_fields.

**Arguments**:

- `attrs (Dict)`: namespace of the class created

**Returns**:

`(Tuple[Dict, Dict])`: namespace of the class updated, dict of extracted model_fields

<a name="models.helpers.models.validate_related_names_in_relations"></a>
#### validate\_related\_names\_in\_relations

```python
validate_related_names_in_relations(model_fields: Dict, new_model: Type["Model"]) -> None
```

Performs a validation of relation_names in relation fields.
If multiple fields are leading to the same related model
only one can have empty related_name param
(populated by default as model.name.lower()+'s').
Also related_names have to be unique for given related model.

**Raises**:

- `ModelDefinitionError`: if validation of related_names fail

**Arguments**:

- `model_fields (Dict[str, ormar.Field])`: dictionary of declared ormar model fields
- `new_model (Model class)`: 

