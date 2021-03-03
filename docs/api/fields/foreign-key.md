<a name="fields.foreign_key"></a>
# fields.foreign\_key

<a name="fields.foreign_key.create_dummy_instance"></a>
#### create\_dummy\_instance

```python
create_dummy_instance(fk: Type["Model"], pk: Any = None) -> "Model"
```

Ormar never returns you a raw data.
So if you have a related field that has a value populated
it will construct you a Model instance out of it.

Creates a "fake" instance of passed Model from pk value.
The instantiated Model has only pk value filled.
To achieve this __pk_only__ flag has to be passed as it skips the validation.

If the nested related Models are required they are set with -1 as pk value.

**Arguments**:

- `fk (Model class)`: class of the related Model to which instance should be constructed
- `pk (Any)`: value of the primary_key column

**Returns**:

`(Model)`: Model instance populated with only pk

<a name="fields.foreign_key.create_dummy_model"></a>
#### create\_dummy\_model

```python
create_dummy_model(base_model: Type["Model"], pk_field: Type[Union[BaseField, "ForeignKeyField", "ManyToManyField"]]) -> Type["BaseModel"]
```

Used to construct a dummy pydantic model for type hints and pydantic validation.
Populates only pk field and set it to desired type.

**Arguments**:

- `base_model (Model class)`: class of target dummy model
- `pk_field (Type[Union[BaseField, "ForeignKeyField", "ManyToManyField"]])`: ormar Field to be set on pydantic Model

**Returns**:

`(pydantic.BaseModel)`: constructed dummy model

<a name="fields.foreign_key.populate_fk_params_based_on_to_model"></a>
#### populate\_fk\_params\_based\_on\_to\_model

```python
populate_fk_params_based_on_to_model(to: Type["Model"], nullable: bool, onupdate: str = None, ondelete: str = None) -> Tuple[Any, List, Any]
```

Based on target to model to which relation leads to populates the type of the
pydantic field to use, ForeignKey constraint and type of the target column field.

**Arguments**:

- `to (Model class)`: target related ormar Model
- `nullable (bool)`: marks field as optional/ required
- `onupdate (str)`: parameter passed to sqlalchemy.ForeignKey.
How to treat child rows on update of parent (the one where FK is defined) model.
- `ondelete (str)`: parameter passed to sqlalchemy.ForeignKey.
How to treat child rows on delete of parent (the one where FK is defined) model.

**Returns**:

`(Tuple[Any, List, Any])`: tuple with target pydantic type, list of fk constraints and target col type

<a name="fields.foreign_key.UniqueColumns"></a>
## UniqueColumns Objects

```python
class UniqueColumns(UniqueConstraint)
```

Subclass of sqlalchemy.UniqueConstraint.
Used to avoid importing anything from sqlalchemy by user.

<a name="fields.foreign_key.ForeignKeyConstraint"></a>
## ForeignKeyConstraint Objects

```python
@dataclass
class ForeignKeyConstraint()
```

Internal container to store ForeignKey definitions used later
to produce sqlalchemy.ForeignKeys

<a name="fields.foreign_key.ForeignKey"></a>
#### ForeignKey

```python
ForeignKey(to: "ToType", *, name: str = None, unique: bool = False, nullable: bool = True, related_name: str = None, virtual: bool = False, onupdate: str = None, ondelete: str = None, **kwargs: Any, ,) -> Any
```

Despite a name it's a function that returns constructed ForeignKeyField.
This function is actually used in model declaration (as ormar.ForeignKey(ToModel)).

Accepts number of relation setting parameters as well as all BaseField ones.

**Arguments**:

- `to (Model class)`: target related ormar Model
- `name (str)`: name of the database field - later called alias
- `unique (bool)`: parameter passed to sqlalchemy.ForeignKey, unique flag
- `nullable (bool)`: marks field as optional/ required
- `related_name (str)`: name of reversed FK relation populated for you on to model
- `virtual (bool)`: marks if relation is virtual.
It is for reversed FK and auto generated FK on through model in Many2Many relations.
- `onupdate (str)`: parameter passed to sqlalchemy.ForeignKey.
How to treat child rows on update of parent (the one where FK is defined) model.
- `ondelete (str)`: parameter passed to sqlalchemy.ForeignKey.
How to treat child rows on delete of parent (the one where FK is defined) model.
- `kwargs (Any)`: all other args to be populated by BaseField

**Returns**:

`(ForeignKeyField)`: ormar ForeignKeyField with relation to selected model

<a name="fields.foreign_key.ForeignKeyField"></a>
## ForeignKeyField Objects

```python
class ForeignKeyField(BaseField)
```

Actual class returned from ForeignKey function call and stored in model_fields.

<a name="fields.foreign_key.ForeignKeyField.get_source_related_name"></a>
#### get\_source\_related\_name

```python
 | @classmethod
 | get_source_related_name(cls) -> str
```

Returns name to use for source relation name.
For FK it's the same, differs for m2m fields.
It's either set as `related_name` or by default it's owner model. get_name + 's'

**Returns**:

`(str)`: name of the related_name or default related name.

<a name="fields.foreign_key.ForeignKeyField.get_related_name"></a>
#### get\_related\_name

```python
 | @classmethod
 | get_related_name(cls) -> str
```

Returns name to use for reverse relation.
It's either set as `related_name` or by default it's owner model. get_name + 's'

**Returns**:

`(str)`: name of the related_name or default related name.

<a name="fields.foreign_key.ForeignKeyField.evaluate_forward_ref"></a>
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

<a name="fields.foreign_key.ForeignKeyField._extract_model_from_sequence"></a>
#### \_extract\_model\_from\_sequence

```python
 | @classmethod
 | _extract_model_from_sequence(cls, value: List, child: "Model", to_register: bool) -> List["Model"]
```

Takes a list of Models and registers them on parent.
Registration is mutual, so children have also reference to parent.

Used in reverse FK relations.

**Arguments**:

- `value (List)`: list of Model
- `child (Model)`: child/ related Model
- `to_register (bool)`: flag if the relation should be set in RelationshipManager

**Returns**:

`(List["Model"])`: list (if needed) registered Models

<a name="fields.foreign_key.ForeignKeyField._register_existing_model"></a>
#### \_register\_existing\_model

```python
 | @classmethod
 | _register_existing_model(cls, value: "Model", child: "Model", to_register: bool) -> "Model"
```

Takes already created instance and registers it for parent.
Registration is mutual, so children have also reference to parent.

Used in reverse FK relations and normal FK for single models.

**Arguments**:

- `value (Model)`: already instantiated Model
- `child (Model)`: child/ related Model
- `to_register (bool)`: flag if the relation should be set in RelationshipManager

**Returns**:

`(Model)`: (if needed) registered Model

<a name="fields.foreign_key.ForeignKeyField._construct_model_from_dict"></a>
#### \_construct\_model\_from\_dict

```python
 | @classmethod
 | _construct_model_from_dict(cls, value: dict, child: "Model", to_register: bool) -> "Model"
```

Takes a dictionary, creates a instance and registers it for parent.
If dictionary contains only one field and it's a pk it is a __pk_only__ model.
Registration is mutual, so children have also reference to parent.

Used in normal FK for dictionaries.

**Arguments**:

- `value (dict)`: dictionary of a Model
- `child (Model)`: child/ related Model
- `to_register (bool)`: flag if the relation should be set in RelationshipManager

**Returns**:

`(Model)`: (if needed) registered Model

<a name="fields.foreign_key.ForeignKeyField._construct_model_from_pk"></a>
#### \_construct\_model\_from\_pk

```python
 | @classmethod
 | _construct_model_from_pk(cls, value: Any, child: "Model", to_register: bool) -> "Model"
```

Takes a pk value, creates a dummy instance and registers it for parent.
Registration is mutual, so children have also reference to parent.

Used in normal FK for dictionaries.

**Arguments**:

- `value (Any)`: value of a related pk / fk column
- `child (Model)`: child/ related Model
- `to_register (bool)`: flag if the relation should be set in RelationshipManager

**Returns**:

`(Model)`: (if needed) registered Model

<a name="fields.foreign_key.ForeignKeyField.register_relation"></a>
#### register\_relation

```python
 | @classmethod
 | register_relation(cls, model: "Model", child: "Model") -> None
```

Registers relation between parent and child in relation manager.
Relation manager is kep on each model (different instance).

Used in Metaclass and sometimes some relations are missing
(i.e. cloned Models in fastapi might miss one).

**Arguments**:

- `model (Model class)`: parent model (with relation definition)
- `child (Model class)`: child model

<a name="fields.foreign_key.ForeignKeyField.has_unresolved_forward_refs"></a>
#### has\_unresolved\_forward\_refs

```python
 | @classmethod
 | has_unresolved_forward_refs(cls) -> bool
```

Verifies if the filed has any ForwardRefs that require updating before the
model can be used.

**Returns**:

`(bool)`: result of the check

<a name="fields.foreign_key.ForeignKeyField.expand_relationship"></a>
#### expand\_relationship

```python
 | @classmethod
 | expand_relationship(cls, value: Any, child: Union["Model", "NewBaseModel"], to_register: bool = True) -> Optional[Union["Model", List["Model"]]]
```

For relations the child model is first constructed (if needed),
registered in relation and returned.
For relation fields the value can be a pk value (Any type of field),
dict (from Model) or actual instance/list of a "Model".

Selects the appropriate constructor based on a passed value.

**Arguments**:

- `value (Any)`: a Model field value, returned untouched for non relation fields.
- `child (Union["Model", "NewBaseModel"])`: a child Model to register
- `to_register (bool)`: flag if the relation should be set in RelationshipManager

**Returns**:

`(Optional[Union["Model", List["Model"]]])`: returns a Model or a list of Models

<a name="fields.foreign_key.ForeignKeyField.get_relation_name"></a>
#### get\_relation\_name

```python
 | @classmethod
 | get_relation_name(cls) -> str
```

Returns name of the relation, which can be a own name or through model
names for m2m models

**Returns**:

`(bool)`: result of the check

<a name="fields.foreign_key.ForeignKeyField.get_source_model"></a>
#### get\_source\_model

```python
 | @classmethod
 | get_source_model(cls) -> Type["Model"]
```

Returns model from which the relation comes -> either owner or through model

**Returns**:

`(Type["Model"])`: source model

