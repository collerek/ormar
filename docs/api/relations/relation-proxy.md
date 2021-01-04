<a name="relations.relation_proxy"></a>
# relations.relation\_proxy

<a name="relations.relation_proxy.RelationProxy"></a>
## RelationProxy Objects

```python
class RelationProxy(list)
```

Proxy of the Relation that is a list with special methods.

<a name="relations.relation_proxy.RelationProxy.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(relation: "Relation", type_: "RelationType", field_name: str, data_: Any = None) -> None
```

<a name="relations.relation_proxy.RelationProxy.related_field_name"></a>
#### related\_field\_name

```python
 | @property
 | related_field_name() -> str
```

On first access calculates the name of the related field, later stored in
_related_field_name property.

**Returns**:

`(str)`: name of the related field

<a name="relations.relation_proxy.RelationProxy.__getattribute__"></a>
#### \_\_getattribute\_\_

```python
 | __getattribute__(item: str) -> Any
```

Since some QuerySetProxy methods overwrite builtin list methods we
catch calls to them and delegate it to QuerySetProxy instead.

**Arguments**:

- `item (str)`: name of attribute

**Returns**:

`(Any)`: value of attribute

<a name="relations.relation_proxy.RelationProxy.__getattr__"></a>
#### \_\_getattr\_\_

```python
 | __getattr__(item: str) -> Any
```

Delegates calls for non existing attributes to QuerySetProxy.

**Arguments**:

- `item (str)`: name of attribute/method

**Returns**:

`(method)`: method from QuerySetProxy if exists

<a name="relations.relation_proxy.RelationProxy._initialize_queryset"></a>
#### \_initialize\_queryset

```python
 | _initialize_queryset() -> None
```

Initializes the QuerySetProxy if not yet initialized.

<a name="relations.relation_proxy.RelationProxy._check_if_queryset_is_initialized"></a>
#### \_check\_if\_queryset\_is\_initialized

```python
 | _check_if_queryset_is_initialized() -> bool
```

Checks if the QuerySetProxy is already set and ready.

**Returns**:

`(bool)`: result of the check

<a name="relations.relation_proxy.RelationProxy._check_if_model_saved"></a>
#### \_check\_if\_model\_saved

```python
 | _check_if_model_saved() -> None
```

Verifies if the parent model of the relation has been already saved.
Otherwise QuerySetProxy cannot filter by parent primary key.

<a name="relations.relation_proxy.RelationProxy._set_queryset"></a>
#### \_set\_queryset

```python
 | _set_queryset() -> "QuerySet"
```

Creates new QuerySet with relation model and pre filters it with currents
parent model primary key, so all queries by definition are already related
to the parent model only, without need for user to filter them.

**Returns**:

`(QuerySet)`: initialized QuerySet

<a name="relations.relation_proxy.RelationProxy.remove"></a>
#### remove

```python
 | async remove(item: "Model", keep_reversed: bool = True) -> None
```

Removes the item from relation with parent.

Through models are automatically deleted for m2m relations.

For reverse FK relations keep_reversed flag marks if the reversed models
should be kept or deleted from the database too (False means that models
will be deleted, and not only removed from relation).

**Arguments**:

- `item (Model)`: child to remove from relation
- `keep_reversed (bool)`: flag if the reversed model should be kept or deleted too

<a name="relations.relation_proxy.RelationProxy.add"></a>
#### add

```python
 | async add(item: "Model") -> None
```

Adds child model to relation.

For ManyToMany relations through instance is automatically created.

**Arguments**:

- `item (Model)`: child to add to relation

