<a name="fields.many_to_many"></a>
# fields.many\_to\_many

<a name="fields.many_to_many.REF_PREFIX"></a>
#### REF\_PREFIX

<a name="fields.many_to_many.ManyToMany"></a>
#### ManyToMany

```python
ManyToMany(to: Type["Model"], through: Type["Model"], *, name: str = None, unique: bool = False, virtual: bool = False, **kwargs: Any) -> Any
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

<a name="fields.many_to_many.ManyToManyField.through"></a>
#### through

<a name="fields.many_to_many.ManyToManyField.default_target_field_name"></a>
#### default\_target\_field\_name

```python
 | @classmethod
 | default_target_field_name(cls) -> str
```

Returns default target model name on through model.

**Returns**:

`(str)`: name of the field

