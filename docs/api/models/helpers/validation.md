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

- `field (BaseField)`: ormar field to check

**Returns**:

`(bool)`: result of the check

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

- `field (BaseField)`: ormar field to check with choices
- `values (Dict)`: current values of the model to verify

**Returns**:

`(Tuple[Any, List])`: value, choices list

<a name="models.helpers.validation.validate_choices"></a>
#### validate\_choices

```python
validate_choices(field: "BaseField", value: Any) -> None
```

Validates if given value is in provided choices.

**Raises**:

- `ValueError`: If value is not in choices.

**Arguments**:

- `field (BaseField)`: field to validate
- `value (Any)`: value of the field

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

- `cls (Model class)`: constructed class
- `values (Dict[str, Any])`: dictionary of field values (pydantic side)

**Returns**:

`(Dict[str, Any])`: values if pass validation, otherwise exception is raised

<a name="models.helpers.validation.construct_modify_schema_function"></a>
#### construct\_modify\_schema\_function

```python
construct_modify_schema_function(fields_with_choices: List) -> SchemaExtraCallable
```

Modifies the schema to include fields with choices validator.
Those fields will be displayed in schema as Enum types with available choices
values listed next to them.

**Arguments**:

- `fields_with_choices (List)`: list of fields with choices validation

**Returns**:

`(Callable)`: callable that will be run by pydantic to modify the schema

<a name="models.helpers.validation.populate_choices_validators"></a>
#### populate\_choices\_validators

```python
populate_choices_validators(model: Type["Model"]) -> None
```

Checks if Model has any fields with choices set.
If yes it adds choices validation into pre root validators.

**Arguments**:

- `model (Model class)`: newly constructed Model

