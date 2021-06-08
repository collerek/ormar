<a name="models.helpers.validation"></a>
# models.helpers.validation

<a name="models.helpers.validation.check_if_field_has_choices"></a>
#### check\_if\_field\_has\_choices

```python
check_if_field_has_choices(field: BaseField) -> bool
```

Checks if given field has choices populated.
A if it has one, a validator for this field needs to be attached.

**Arguments**:

- `field` (`BaseField`): ormar field to check

**Returns**:

`bool`: result of the check

<a name="models.helpers.validation.convert_choices_if_needed"></a>
#### convert\_choices\_if\_needed

```python
convert_choices_if_needed(field: "BaseField", value: Any) -> Tuple[Any, List]
```

Converts dates to isoformat as fastapi can check this condition in routes
and the fields are not yet parsed.

Converts enums to list of it's values.

Converts uuids to strings.

Converts decimal to float with given scale.

**Arguments**:

- `field` (`BaseField`): ormar field to check with choices
- `values` (`Dict`): current values of the model to verify

**Returns**:

`Tuple[Any, List]`: value, choices list

<a name="models.helpers.validation.validate_choices"></a>
#### validate\_choices

```python
validate_choices(field: "BaseField", value: Any) -> None
```

Validates if given value is in provided choices.

**Raises**:

- `ValueError`: If value is not in choices.

**Arguments**:

- `field` (`BaseField`): field to validate
- `value` (`Any`): value of the field

<a name="models.helpers.validation.choices_validator"></a>
#### choices\_validator

```python
choices_validator(cls: Type["Model"], values: Dict[str, Any]) -> Dict[str, Any]
```

Validator that is attached to pydantic model pre root validators.
Validator checks if field value is in field.choices list.

**Raises**:

- `ValueError`: if field value is outside of allowed choices.

**Arguments**:

- `cls` (`Model class`): constructed class
- `values` (`Dict[str, Any]`): dictionary of field values (pydantic side)

**Returns**:

`Dict[str, Any]`: values if pass validation, otherwise exception is raised

<a name="models.helpers.validation.generate_model_example"></a>
#### generate\_model\_example

```python
generate_model_example(model: Type["Model"], relation_map: Dict = None) -> Dict
```

Generates example to be included in schema in fastapi.

**Arguments**:

- `model` (`Type["Model"]`): ormar.Model
- `relation_map` (`Optional[Dict]`): dict with relations to follow

**Returns**:

`Dict[str, int]`: dict with example values

<a name="models.helpers.validation.populates_sample_fields_values"></a>
#### populates\_sample\_fields\_values

```python
populates_sample_fields_values(example: Dict[str, Any], name: str, field: BaseField, relation_map: Dict = None) -> None
```

Iterates the field and sets fields to sample values

**Arguments**:

- `field` (`BaseField`): ormar field
- `name` (`str`): name of the field
- `example` (`Dict[str, Any]`): example dict
- `relation_map` (`Optional[Dict]`): dict with relations to follow

<a name="models.helpers.validation.get_nested_model_example"></a>
#### get\_nested\_model\_example

```python
get_nested_model_example(name: str, field: "BaseField", relation_map: Dict) -> Union[List, Dict]
```

Gets representation of nested model.

**Arguments**:

- `name` (`str`): name of the field to follow
- `field` (`BaseField`): ormar field
- `relation_map` (`Dict`): dict with relation map

**Returns**:

`Union[List, Dict]`: nested model or list of nested model repr

<a name="models.helpers.validation.generate_pydantic_example"></a>
#### generate\_pydantic\_example

```python
generate_pydantic_example(pydantic_model: Type[pydantic.BaseModel], exclude: Set = None) -> Dict
```

Generates dict with example.

**Arguments**:

- `pydantic_model` (`Type[pydantic.BaseModel]`): model to parse
- `exclude` (`Optional[Set]`): list of fields to exclude

**Returns**:

`Dict`: dict with fields and sample values

<a name="models.helpers.validation.get_pydantic_example_repr"></a>
#### get\_pydantic\_example\_repr

```python
get_pydantic_example_repr(type_: Any) -> Any
```

Gets sample representation of pydantic field for example dict.

**Arguments**:

- `type_` (`Any`): type of pydantic field

**Returns**:

`Any`: representation to include in example

<a name="models.helpers.validation.overwrite_example_and_description"></a>
#### overwrite\_example\_and\_description

```python
overwrite_example_and_description(schema: Dict[str, Any], model: Type["Model"]) -> None
```

Overwrites the example with properly nested children models.
Overwrites the description if it's taken from ormar.Model.

**Arguments**:

- `schema` (`Dict[str, Any]`): schema of current model
- `model` (`Type["Model"]`): model class

<a name="models.helpers.validation.overwrite_binary_format"></a>
#### overwrite\_binary\_format

```python
overwrite_binary_format(schema: Dict[str, Any], model: Type["Model"]) -> None
```

Overwrites format of the field if it's a LargeBinary field with
a flag to represent the field as base64 encoded string.

**Arguments**:

- `schema` (`Dict[str, Any]`): schema of current model
- `model` (`Type["Model"]`): model class

<a name="models.helpers.validation.construct_modify_schema_function"></a>
#### construct\_modify\_schema\_function

```python
construct_modify_schema_function(fields_with_choices: List) -> SchemaExtraCallable
```

Modifies the schema to include fields with choices validator.
Those fields will be displayed in schema as Enum types with available choices
values listed next to them.

Note that schema extra has to be a function, otherwise it's called to soon
before all the relations are expanded.

**Arguments**:

- `fields_with_choices` (`List`): list of fields with choices validation

**Returns**:

`Callable`: callable that will be run by pydantic to modify the schema

<a name="models.helpers.validation.construct_schema_function_without_choices"></a>
#### construct\_schema\_function\_without\_choices

```python
construct_schema_function_without_choices() -> SchemaExtraCallable
```

Modifies model example and description if needed.

Note that schema extra has to be a function, otherwise it's called to soon
before all the relations are expanded.

**Returns**:

`Callable`: callable that will be run by pydantic to modify the schema

<a name="models.helpers.validation.populate_choices_validators"></a>
#### populate\_choices\_validators

```python
populate_choices_validators(model: Type["Model"]) -> None
```

Checks if Model has any fields with choices set.
If yes it adds choices validation into pre root validators.

**Arguments**:

- `model` (`Model class`): newly constructed Model

