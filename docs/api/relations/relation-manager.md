<a name="relations.relation_manager"></a>
# relations.relation\_manager

<a name="relations.relation_manager.RelationsManager"></a>
## RelationsManager Objects

```python
class RelationsManager()
```

Manages relations on a Model, each Model has it's own instance.

<a name="relations.relation_manager.RelationsManager.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(related_fields: List[Type[ForeignKeyField]] = None, owner: "NewBaseModel" = None) -> None
```

<a name="relations.relation_manager.RelationsManager._get_relation_type"></a>
#### \_get\_relation\_type

```python
 | _get_relation_type(field: Type[BaseField]) -> RelationType
```

Returns type of the relation declared on a field.

**Arguments**:

- `field (Type[BaseField])`: field with relation declaration

**Returns**:

`(RelationType)`: type of the relation defined on field

<a name="relations.relation_manager.RelationsManager._add_relation"></a>
#### \_add\_relation

```python
 | _add_relation(field: Type[BaseField]) -> None
```

Registers relation in the manager.
Adds Relation instance under field.name.

**Arguments**:

- `field (Type[BaseField])`: field with relation declaration

<a name="relations.relation_manager.RelationsManager.__contains__"></a>
#### \_\_contains\_\_

```python
 | __contains__(item: str) -> bool
```

Checks if relation with given name is already registered.

**Arguments**:

- `item (str)`: name of attribute

**Returns**:

`(bool)`: result of the check

<a name="relations.relation_manager.RelationsManager.get"></a>
#### get

```python
 | get(name: str) -> Optional[Union["T", Sequence["T"]]]
```

Returns the related model/models if relation is set.
Actual call is delegated to Relation instance registered under relation name.

**Arguments**:

- `name (str)`: name of the relation

**Returns**:

`(Optional[Union[Model, List[Model]])`: related model or list of related models if set

<a name="relations.relation_manager.RelationsManager._get"></a>
#### \_get

```python
 | _get(name: str) -> Optional[Relation]
```

Returns the actual relation and not the related model(s).

**Arguments**:

- `name (str)`: name of the relation

**Returns**:

`(ormar.relations.relation.Relation)`: Relation instance

<a name="relations.relation_manager.RelationsManager.add"></a>
#### add

```python
 | @staticmethod
 | add(parent: "Model", child: "Model", child_name: str, virtual: bool, relation_name: str) -> None
```

Adds relation on both sides -> meaning on both child and parent models.
One side of the relation is always weakref proxy to avoid circular refs.

Based on the side from which relation is added and relation name actual names
of parent and child relations are established. The related models are registered
on both ends.

**Arguments**:

- `parent (Model)`: parent model on which relation should be registered
- `child (Model)`: child model to register
- `child_name (str)`: potential child name used if related name is not set
- `virtual (bool)`: 
- `relation_name (str)`: name of the relation

<a name="relations.relation_manager.RelationsManager.remove"></a>
#### remove

```python
 | remove(name: str, child: Union["NewBaseModel", Type["NewBaseModel"]]) -> None
```

Removes given child from relation with given name.
Since you can have many relations between two models you need to pass a name
of relation from which you want to remove the child.

**Arguments**:

- `name (str)`: name of the relation
- `child (Union[Model, Type[Model]])`: child to remove from relation

<a name="relations.relation_manager.RelationsManager.remove_parent"></a>
#### remove\_parent

```python
 | @staticmethod
 | remove_parent(item: Union["NewBaseModel", Type["NewBaseModel"]], parent: "Model", name: str) -> None
```

Removes given parent from relation with given name.
Since you can have many relations between two models you need to pass a name
of relation from which you want to remove the parent.

**Arguments**:

- `item (Union[Model, Type[Model]])`: model with parent registered
- `parent (Model)`: parent Model
- `name (str)`: name of the relation

