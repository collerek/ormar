<a name="relations.utils"></a>
# relations.utils

<a name="relations.utils.get_relations_sides_and_names"></a>
#### get\_relations\_sides\_and\_names

```python
get_relations_sides_and_names(to_field: ForeignKeyField, parent: "Model", child: "Model") -> Tuple["Model", "Model", str, str]
```

Determines the names of child and parent relations names, as well as
changes one of the sides of the relation into weakref.proxy to model.

**Arguments**:

- `to_field (ForeignKeyField)`: field with relation definition
- `parent (Model)`: parent model
- `child (Model)`: child model

**Returns**:

`(Tuple["Model", "Model", str, str])`: parent, child, child_name, to_name

