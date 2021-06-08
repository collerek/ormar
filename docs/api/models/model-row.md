<a name="models.model_row"></a>
# models.model\_row

<a name="models.model_row.ModelRow"></a>
## ModelRow Objects

```python
class ModelRow(NewBaseModel)
```

<a name="models.model_row.ModelRow.from_row"></a>
#### from\_row

```python
 | @classmethod
 | from_row(cls, row: sqlalchemy.engine.ResultProxy, source_model: Type["Model"], select_related: List = None, related_models: Any = None, related_field: "ForeignKeyField" = None, excludable: ExcludableItems = None, current_relation_str: str = "", proxy_source_model: Optional[Type["Model"]] = None, used_prefixes: List[str] = None) -> Optional["Model"]
```

Model method to convert raw sql row from database into ormar.Model instance.
Traverses nested models if they were specified in select_related for query.

Called recurrently and returns model instance if it's present in the row.
Note that it's processing one row at a time, so if there are duplicates of
parent row that needs to be joined/combined
(like parent row in sql join with 2+ child rows)
instances populated in this method are later combined in the QuerySet.
Other method working directly on raw database results is in prefetch_query,
where rows are populated in a different way as they do not have
nested models in result.

**Arguments**:

- `used_prefixes` (`List[str]`): list of already extracted prefixes
- `proxy_source_model` (`Optional[Type["ModelRow"]]`): source model from which querysetproxy is constructed
- `excludable` (`ExcludableItems`): structure of fields to include and exclude
- `current_relation_str` (`str`): name of the relation field
- `source_model` (`Type[Model]`): model on which relation was defined
- `row` (`sqlalchemy.engine.result.ResultProxy`): raw result row from the database
- `select_related` (`List`): list of names of related models fetched from database
- `related_models` (`Union[List, Dict]`): list or dict of related models
- `related_field` (`ForeignKeyField`): field with relation declaration

**Returns**:

`Optional[Model]`: returns model if model is populated from database

<a name="models.model_row.ModelRow._process_table_prefix"></a>
#### \_process\_table\_prefix

```python
 | @classmethod
 | _process_table_prefix(cls, source_model: Type["Model"], current_relation_str: str, related_field: "ForeignKeyField", used_prefixes: List[str]) -> str
```

**Arguments**:

- `source_model` (`Type[Model]`): model on which relation was defined
- `current_relation_str` (`str`): current relation string
- `related_field` (`"ForeignKeyField"`): field with relation declaration
- `used_prefixes` (`List[str]`): list of already extracted prefixes

**Returns**:

`str`: table_prefix to use

<a name="models.model_row.ModelRow._populate_nested_models_from_row"></a>
#### \_populate\_nested\_models\_from\_row

```python
 | @classmethod
 | _populate_nested_models_from_row(cls, item: dict, row: sqlalchemy.engine.ResultProxy, source_model: Type["Model"], related_models: Any, excludable: ExcludableItems, table_prefix: str, used_prefixes: List[str], current_relation_str: str = None, proxy_source_model: Type["Model"] = None) -> dict
```

Traverses structure of related models and populates the nested models
from the database row.
Related models can be a list if only directly related models are to be
populated, converted to dict if related models also have their own related
models to be populated.

Recurrently calls from_row method on nested instances and create nested
instances. In the end those instances are added to the final model dictionary.

**Arguments**:

- `proxy_source_model` (`Optional[Type["ModelRow"]]`): source model from which querysetproxy is constructed
- `excludable` (`ExcludableItems`): structure of fields to include and exclude
- `source_model` (`Type[Model]`): source model from which relation started
- `current_relation_str` (`str`): joined related parts into one string
- `item` (`Dict`): dictionary of already populated nested models, otherwise empty dict
- `row` (`sqlalchemy.engine.result.ResultProxy`): raw result row from the database
- `related_models` (`Union[Dict, List]`): list or dict of related models

**Returns**:

`Dict`: dictionary with keys corresponding to model fields names

<a name="models.model_row.ModelRow._process_remainder_and_relation_string"></a>
#### \_process\_remainder\_and\_relation\_string

```python
 | @staticmethod
 | _process_remainder_and_relation_string(related_models: Union[Dict, List], current_relation_str: Optional[str], related: str) -> Tuple[str, Optional[Union[Dict, List]]]
```

Process remainder models and relation string

**Arguments**:

- `related_models` (`Union[Dict, List]`): list or dict of related models
- `current_relation_str` (`Optional[str]`): current relation string
- `related` (`str`): name of the relation

<a name="models.model_row.ModelRow._populate_through_instance"></a>
#### \_populate\_through\_instance

```python
 | @classmethod
 | _populate_through_instance(cls, row: sqlalchemy.engine.ResultProxy, item: Dict, related: str, excludable: ExcludableItems, child: "Model", proxy_source_model: Optional[Type["Model"]]) -> None
```

Populates the through model on reverse side of current query.
Normally it's child class, unless the query is from queryset.

**Arguments**:

- `row` (`sqlalchemy.engine.ResultProxy`): row from db result
- `item` (`Dict`): parent item dict
- `related` (`str`): current relation name
- `excludable` (`ExcludableItems`): structure of fields to include and exclude
- `child` (`"Model"`): child item of parent
- `proxy_source_model` (`Type["Model"]`): source model from which querysetproxy is constructed

<a name="models.model_row.ModelRow._create_through_instance"></a>
#### \_create\_through\_instance

```python
 | @classmethod
 | _create_through_instance(cls, row: sqlalchemy.engine.ResultProxy, through_name: str, related: str, excludable: ExcludableItems) -> "ModelRow"
```

Initialize the through model from db row.
Excluded all relation fields and other exclude/include set in excludable.

**Arguments**:

- `row` (`sqlalchemy.engine.ResultProxy`): loaded row from database
- `through_name` (`str`): name of the through field
- `related` (`str`): name of the relation
- `excludable` (`ExcludableItems`): structure of fields to include and exclude

**Returns**:

`"ModelRow"`: initialized through model without relation

<a name="models.model_row.ModelRow.extract_prefixed_table_columns"></a>
#### extract\_prefixed\_table\_columns

```python
 | @classmethod
 | extract_prefixed_table_columns(cls, item: dict, row: sqlalchemy.engine.result.ResultProxy, table_prefix: str, excludable: ExcludableItems) -> Dict
```

Extracts own fields from raw sql result, using a given prefix.
Prefix changes depending on the table's position in a join.

If the table is a main table, there is no prefix.
All joined tables have prefixes to allow duplicate column names,
as well as duplicated joins to the same table from multiple different tables.

Extracted fields populates the related dict later used to construct a Model.

Used in Model.from_row and PrefetchQuery._populate_rows methods.

**Arguments**:

each pair of tables have own prefix (two of them depending on direction) -
used in joins to allow multiple joins to the same table.
- `excludable` (`ExcludableItems`): structure of fields to include and exclude
- `item` (`Dict`): dictionary of already populated nested models, otherwise empty dict
- `row` (`sqlalchemy.engine.result.ResultProxy`): raw result row from the database
- `table_prefix` (`str`): prefix of the table from AliasManager

**Returns**:

`Dict`: dictionary with keys corresponding to model fields names

