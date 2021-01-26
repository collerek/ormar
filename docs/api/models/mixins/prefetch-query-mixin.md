<a name="models.mixins.prefetch_mixin"></a>
# models.mixins.prefetch\_mixin

<a name="models.mixins.prefetch_mixin.PrefetchQueryMixin"></a>
## PrefetchQueryMixin Objects

```python
class PrefetchQueryMixin(RelationMixin)
```

Used in PrefetchQuery to extract ids and names of models to prefetch.

<a name="models.mixins.prefetch_mixin.PrefetchQueryMixin.get_clause_target_and_filter_column_name"></a>
#### get\_clause\_target\_and\_filter\_column\_name

```python
 | @staticmethod
 | get_clause_target_and_filter_column_name(parent_model: Type["Model"], target_model: Type["Model"], reverse: bool, related: str) -> Tuple[Type["Model"], str]
```

Returns Model on which query clause should be performed and name of the column.

**Arguments**:

- `parent_model (Type[Model])`: related model that the relation lead to
- `target_model (Type[Model])`: model on which query should be perfomed
- `reverse (bool)`: flag if the relation is reverse
- `related (str)`: name of the relation field

**Returns**:

`(Tuple[Type[Model], str])`: Model on which query clause should be performed and name of the column

<a name="models.mixins.prefetch_mixin.PrefetchQueryMixin.get_column_name_for_id_extraction"></a>
#### get\_column\_name\_for\_id\_extraction

```python
 | @staticmethod
 | get_column_name_for_id_extraction(parent_model: Type["Model"], reverse: bool, related: str, use_raw: bool) -> str
```

Returns name of the column that should be used to extract ids from model.
Depending on the relation side it's either primary key column of parent model
or field name specified by related parameter.

**Arguments**:

- `parent_model (Type[Model])`: model from which id column should be extracted
- `reverse (bool)`: flag if the relation is reverse
- `related (str)`: name of the relation field
- `use_raw (bool)`: flag if aliases or field names should be used

**Returns**:

`()`: 

<a name="models.mixins.prefetch_mixin.PrefetchQueryMixin.get_related_field_name"></a>
#### get\_related\_field\_name

```python
 | @classmethod
 | get_related_field_name(cls, target_field: Type["ForeignKeyField"]) -> str
```

Returns name of the relation field that should be used in prefetch query.
This field is later used to register relation in prefetch query,
populate relations dict, and populate nested model in prefetch query.

**Arguments**:

- `target_field (Type[BaseField])`: relation field that should be used in prefetch

**Returns**:

`(str)`: name of the field

<a name="models.mixins.prefetch_mixin.PrefetchQueryMixin.get_filtered_names_to_extract"></a>
#### get\_filtered\_names\_to\_extract

```python
 | @classmethod
 | get_filtered_names_to_extract(cls, prefetch_dict: Dict) -> List
```

Returns list of related fields names that should be followed to prefetch related
models from.

List of models is translated into dict to assure each model is extracted only
once in one query, that's why this function accepts prefetch_dict not list.

Only relations from current model are returned.

**Arguments**:

- `prefetch_dict (Dict)`: dictionary of fields to extract

**Returns**:

`(List)`: list of fields names to extract

