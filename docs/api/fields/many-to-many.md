<a name="fields.many_to_many"></a>
# fields.many\_to\_many

<a name="fields.many_to_many.populate_m2m_params_based_on_to_model"></a>
#### populate\_m2m\_params\_based\_on\_to\_model

```python
populate_m2m_params_based_on_to_model(to: Type["Model"], nullable: bool) -> Tuple[Any, Any]
```

Based on target to model to which relation leads to populates the type of the
pydantic field to use and type of the target column field.

**Arguments**:

- `to (Model class)`: target related ormar Model
- `nullable (bool)`: marks field as optional/ required

**Returns**:

`(tuple with target pydantic type and target col type)`: Tuple[List, Any]

<a name="fields.many_to_many.ManyToMany"></a>
#### ManyToMany

```python
ManyToMany(to: "ToType", through: "ToType", *, name: str = None, unique: bool = False, virtual: bool = False, **kwargs: Any, ,) -> Any
```

Despite a name it's a function that returns constructed ManyToManyField.
This function is actually used in model declaration
(as ormar.ManyToMany(ToModel, through=ThroughModel)).

Accepts number of relation setting parameters as well as all BaseField ones.

**Arguments**:

- `to (Model class)`: target related ormar Model
- `through (Model class)`: through model for m2m relation
- `name (str)`: name of the database field - later called alias
- `unique (bool)`: parameter passed to sqlalchemy.ForeignKey, unique flag
- `virtual (bool)`: marks if relation is virtual.
It is for reversed FK and auto generated FK on through model in Many2Many relations.
- `kwargs (Any)`: all other args to be populated by BaseField

**Returns**:

`(ManyToManyField)`: ormar ManyToManyField with m2m relation to selected model

<a name="fields.many_to_many.ManyToManyField"></a>
## ManyToManyField Objects

```python
class ManyToManyField(ForeignKeyField,  ormar.QuerySetProtocol,  ormar.RelationProtocol)
```

Actual class returned from ManyToMany function call and stored in model_fields.

<a name="fields.many_to_many.ManyToManyField.get_source_related_name"></a>
#### get\_source\_related\_name

```python
 | @classmethod
 | get_source_related_name(cls) -> str
```

Returns name to use for source relation name.
For FK it's the same, differs for m2m fields.
It's either set as `related_name` or by default it's field name.

**Returns**:

`(str)`: name of the related_name or default related name.

<a name="fields.many_to_many.ManyToManyField.default_target_field_name"></a>
#### default\_target\_field\_name

```python
 | @classmethod
 | default_target_field_name(cls) -> str
```

Returns default target model name on through model.

**Returns**:

`(str)`: name of the field

<a name="fields.many_to_many.ManyToManyField.default_source_field_name"></a>
#### default\_source\_field\_name

```python
 | @classmethod
 | default_source_field_name(cls) -> str
```

Returns default target model name on through model.

**Returns**:

`(str)`: name of the field

<a name="fields.many_to_many.ManyToManyField.has_unresolved_forward_refs"></a>
#### has\_unresolved\_forward\_refs

```python
 | @classmethod
 | has_unresolved_forward_refs(cls) -> bool
```

Verifies if the filed has any ForwardRefs that require updating before the
model can be used.

**Returns**:

`(bool)`: result of the check

<a name="fields.many_to_many.ManyToManyField.evaluate_forward_ref"></a>
#### evaluate\_forward\_ref

```python
 | @classmethod
 | evaluate_forward_ref(cls, globalns: Any, localns: Any) -> None
```

Evaluates the ForwardRef to actual Field based on global and local namespaces

**Arguments**:

- `globalns (Any)`: global namespace
- `localns (Any)`: local namespace

**Returns**:

`(None)`: None

