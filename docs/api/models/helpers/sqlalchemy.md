<a name="models.helpers.sqlalchemy"></a>
# models.helpers.sqlalchemy

<a name="models.helpers.sqlalchemy.adjust_through_many_to_many_model"></a>
#### adjust\_through\_many\_to\_many\_model

```python
adjust_through_many_to_many_model(model_field: "ManyToManyField") -> None
```

Registers m2m relation on through model.
Sets ormar.ForeignKey from through model to both child and parent models.
Sets sqlalchemy.ForeignKey to both child and parent models.
Sets pydantic fields with child and parent model types.

**Arguments**:

- `model_field` (`ManyToManyField`): relation field defined in parent model

<a name="models.helpers.sqlalchemy.create_and_append_m2m_fk"></a>
#### create\_and\_append\_m2m\_fk

```python
create_and_append_m2m_fk(model: Type["Model"], model_field: "ManyToManyField", field_name: str) -> None
```

Registers sqlalchemy Column with sqlalchemy.ForeignKey leading to the model.

Newly created field is added to m2m relation through model Meta columns and table.

**Arguments**:

- `field_name` (`str`): name of the column to create
- `model` (`Model class`): Model class to which FK should be created
- `model_field` (`ManyToManyField field`): field with ManyToMany relation

<a name="models.helpers.sqlalchemy.check_pk_column_validity"></a>
#### check\_pk\_column\_validity

```python
check_pk_column_validity(field_name: str, field: "BaseField", pkname: Optional[str]) -> Optional[str]
```

Receives the field marked as primary key and verifies if the pkname
was not already set (only one allowed per model) and if field is not marked
as pydantic_only as it needs to be a database field.

**Raises**:

- `ModelDefintionError`: if pkname already set or field is pydantic_only

**Arguments**:

- `field_name` (`str`): name of field
- `field` (`BaseField`): ormar.Field
- `pkname` (`Optional[str]`): already set pkname

**Returns**:

`str`: name of the field that should be set as pkname

<a name="models.helpers.sqlalchemy.sqlalchemy_columns_from_model_fields"></a>
#### sqlalchemy\_columns\_from\_model\_fields

```python
sqlalchemy_columns_from_model_fields(model_fields: Dict, new_model: Type["Model"]) -> Tuple[Optional[str], List[sqlalchemy.Column]]
```

Iterates over declared on Model model fields and extracts fields that
should be treated as database fields.

If the model is empty it sets mandatory id field as primary key
(used in through models in m2m relations).

Triggers a validation of relation_names in relation fields. If multiple fields
are leading to the same related model only one can have empty related_name param.
Also related_names have to be unique.

Trigger validation of primary_key - only one and required pk can be set,
cannot be pydantic_only.

Append fields to columns if it's not pydantic_only,
virtual ForeignKey or ManyToMany field.

Sets `owner` on each model_field as reference to newly created Model.

**Raises**:

- `ModelDefinitionError`: if validation of related_names fail,
or pkname validation fails.

**Arguments**:

- `model_fields` (`Dict[str, ormar.Field]`): dictionary of declared ormar model fields
- `new_model` (`Model class`): 

**Returns**:

`Tuple[Optional[str], List[sqlalchemy.Column]]`: pkname, list of sqlalchemy columns

<a name="models.helpers.sqlalchemy._process_fields"></a>
#### \_process\_fields

```python
_process_fields(model_fields: Dict, new_model: Type["Model"]) -> Tuple[Optional[str], List[sqlalchemy.Column]]
```

Helper method.

Populates pkname and columns.
Trigger validation of primary_key - only one and required pk can be set,
cannot be pydantic_only.

Append fields to columns if it's not pydantic_only,
virtual ForeignKey or ManyToMany field.

Sets `owner` on each model_field as reference to newly created Model.

**Raises**:

- `ModelDefinitionError`: if validation of related_names fail,
or pkname validation fails.

**Arguments**:

- `model_fields` (`Dict[str, ormar.Field]`): dictionary of declared ormar model fields
- `new_model` (`Model class`): 

**Returns**:

`Tuple[Optional[str], List[sqlalchemy.Column]]`: pkname, list of sqlalchemy columns

<a name="models.helpers.sqlalchemy._is_through_model_not_set"></a>
#### \_is\_through\_model\_not\_set

```python
_is_through_model_not_set(field: "BaseField") -> bool
```

Alias to if check that verifies if through model was created.

**Arguments**:

- `field` (`"BaseField"`): field to check

**Returns**:

`bool`: result of the check

<a name="models.helpers.sqlalchemy._is_db_field"></a>
#### \_is\_db\_field

```python
_is_db_field(field: "BaseField") -> bool
```

Alias to if check that verifies if field should be included in database.

**Arguments**:

- `field` (`"BaseField"`): field to check

**Returns**:

`bool`: result of the check

<a name="models.helpers.sqlalchemy.populate_meta_tablename_columns_and_pk"></a>
#### populate\_meta\_tablename\_columns\_and\_pk

```python
populate_meta_tablename_columns_and_pk(name: str, new_model: Type["Model"]) -> Type["Model"]
```

Sets Model tablename if it's not already set in Meta.
Default tablename if not present is class name lower + s (i.e. Bed becomes -> beds)

Checks if Model's Meta have pkname and columns set.
If not calls the sqlalchemy_columns_from_model_fields to populate
columns from ormar.fields definitions.

**Raises**:

- `ModelDefinitionError`: if pkname is not present raises ModelDefinitionError.
Each model has to have pk.

**Arguments**:

- `name` (`str`): name of the current Model
- `new_model` (`ormar.models.metaclass.ModelMetaclass`): currently constructed Model

**Returns**:

`ormar.models.metaclass.ModelMetaclass`: Model with populated pkname and columns in Meta

<a name="models.helpers.sqlalchemy.check_for_null_type_columns_from_forward_refs"></a>
#### check\_for\_null\_type\_columns\_from\_forward\_refs

```python
check_for_null_type_columns_from_forward_refs(meta: "ModelMeta") -> bool
```

Check is any column is of NUllType() meaning it's empty column from ForwardRef

**Arguments**:

- `meta` (`Model class Meta`): Meta class of the Model without sqlalchemy table constructed

**Returns**:

`bool`: result of the check

<a name="models.helpers.sqlalchemy.populate_meta_sqlalchemy_table_if_required"></a>
#### populate\_meta\_sqlalchemy\_table\_if\_required

```python
populate_meta_sqlalchemy_table_if_required(meta: "ModelMeta") -> None
```

Constructs sqlalchemy table out of columns and parameters set on Meta class.
It populates name, metadata, columns and constraints.

**Arguments**:

- `meta` (`Model class Meta`): Meta class of the Model without sqlalchemy table constructed

**Returns**:

`Model class`: class with populated Meta.table

<a name="models.helpers.sqlalchemy.update_column_definition"></a>
#### update\_column\_definition

```python
update_column_definition(model: Union[Type["Model"], Type["NewBaseModel"]], field: "ForeignKeyField") -> None
```

Updates a column with a new type column based on updated parameters in FK fields.

**Arguments**:

- `model` (`Type["Model"]`): model on which columns needs to be updated
- `field` (`ForeignKeyField`): field with column definition that requires update

**Returns**:

`None`: None

