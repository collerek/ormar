<a name="models.mixins.merge_mixin"></a>
# models.mixins.merge\_mixin

<a name="models.mixins.merge_mixin.MergeModelMixin"></a>
## MergeModelMixin Objects

```python
class MergeModelMixin()
```

Used to merge models instances returned by database,
but already initialized to ormar Models.keys

Models can duplicate during joins when parent model has multiple child rows,
in the end all parent (main) models should be unique.

<a name="models.mixins.merge_mixin.MergeModelMixin.merge_instances_list"></a>
#### merge\_instances\_list

```python
 | @classmethod
 | merge_instances_list(cls, result_rows: List["Model"]) -> List["Model"]
```

Merges a list of models into list of unique models.

Models can duplicate during joins when parent model has multiple child rows,
in the end all parent (main) models should be unique.

**Arguments**:

populated, each instance is one row in db and some models can duplicate
- `result_rows` (`List["Model"]`): list of already initialized Models with child models

**Returns**:

`List["Model"]`: list of merged models where each main model is unique

<a name="models.mixins.merge_mixin.MergeModelMixin.merge_two_instances"></a>
#### merge\_two\_instances

```python
 | @classmethod
 | merge_two_instances(cls, one: "Model", other: "Model", relation_map: Dict = None) -> "Model"
```

Merges current (other) Model and previous one (one) and returns the current
Model instance with data merged from previous one.

If needed it's calling itself recurrently and merges also children models.

**Arguments**:

- `relation_map` (`Dict`): map of models relations to follow
- `one` (`Model`): previous model instance
- `other` (`Model`): current model instance

**Returns**:

`Model`: current Model instance with data merged from previous one.

<a name="models.mixins.merge_mixin.MergeModelMixin._merge_items_lists"></a>
#### \_merge\_items\_lists

```python
 | @classmethod
 | _merge_items_lists(cls, field_name: str, current_field: List, other_value: List, relation_map: Optional[Dict]) -> List
```

Takes two list of nested models and process them going deeper
according with the map.

If model from one's list is in other -> they are merged with relations
to follow passed from map.

If one's model is not in other it's simply appended to the list.

**Arguments**:

- `field_name` (`str`): name of the current relation field
- `current_field` (`List[Model]`): list of nested models from one model
- `other_value` (`List[Model]`): list of nested models from other model
- `relation_map` (`Dict`): map of relations to follow

**Returns**:

`List[Model]`: merged list of models

