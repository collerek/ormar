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
 | merge_instances_list(cls, result_rows: Sequence["Model"]) -> Sequence["Model"]
```

Merges a list of models into list of unique models.

Models can duplicate during joins when parent model has multiple child rows,
in the end all parent (main) models should be unique.

**Arguments**:

- `result_rows (List["Model"])`: list of already initialized Models with child models
populated, each instance is one row in db and some models can duplicate

**Returns**:

`(List["Model"])`: list of merged models where each main model is unique

<a name="models.mixins.merge_mixin.MergeModelMixin.merge_two_instances"></a>
#### merge\_two\_instances

```python
 | @classmethod
 | merge_two_instances(cls, one: "Model", other: "Model") -> "Model"
```

Merges current (other) Model and previous one (one) and returns the current
Model instance with data merged from previous one.

If needed it's calling itself recurrently and merges also children models.

**Arguments**:

- `one (Model)`: previous model instance
- `other (Model)`: current model instance

**Returns**:

`(Model)`: current Model instance with data merged from previous one.

