<a name="queryset.prefetch_query"></a>
# queryset.prefetch\_query

<a name="queryset.prefetch_query.sort_models"></a>
#### sort\_models

```python
sort_models(models: List["Model"], orders_by: Dict) -> List["Model"]
```

Since prefetch query gets all related models by ids the sorting needs to happen in
python. Since by default models are already sorted by id here we resort only if
order_by parameters was set.

**Arguments**:

- `models` (`List[tests.test_prefetch_related.Division]`): list of models already fetched from db
- `orders_by` (`Dict[str, str]`): order by dictionary

**Returns**:

`List[tests.test_prefetch_related.Division]`: sorted list of models

<a name="queryset.prefetch_query.set_children_on_model"></a>
#### set\_children\_on\_model

```python
set_children_on_model(model: "Model", related: str, children: Dict, model_id: int, models: Dict, orders_by: Dict) -> None
```

Extract ids of child models by given relation id key value.

Based on those ids the actual children model instances are fetched from
already fetched data.

If needed the child models are resorted according to passed orders_by dict.

Also relation is registered as each child is set as parent related field name value.

**Arguments**:

- `model` (`Model`): parent model instance
- `related` (`str`): name of the related field
- `children` (`Dict[int, set]`): dictionary of children ids/ related field value
- `model_id` (`int`): id of the model on which children should be set
- `models` (`Dict`): dictionary of child models instances
- `orders_by` (`Dict`): order_by dictionary

<a name="queryset.prefetch_query.PrefetchQuery"></a>
## PrefetchQuery Objects

```python
class PrefetchQuery()
```

Query used to fetch related models in subsequent queries.
Each model is fetched only ones by the name of the relation.
That means that for each prefetch_related entry next query is issued to database.

<a name="queryset.prefetch_query.PrefetchQuery.prefetch_related"></a>
#### prefetch\_related

```python
 | async prefetch_related(models: Sequence["Model"], rows: List) -> Sequence["Model"]
```

Main entry point for prefetch_query.

Receives list of already initialized parent models with all children from
select_related already populated. Receives also list of row sql result rows
as it's quicker to extract ids that way instead of calling each model.

Returns list with related models already prefetched and set.

**Arguments**:

- `models` (`List[Model]`): list of already instantiated models from main query
- `rows` (`List[sqlalchemy.engine.result.RowProxy]`): row sql result of the main query before the prefetch

**Returns**:

`List[Model]`: list of models with children prefetched

<a name="queryset.prefetch_query.PrefetchQuery._extract_ids_from_raw_data"></a>
#### \_extract\_ids\_from\_raw\_data

```python
 | _extract_ids_from_raw_data(parent_model: Type["Model"], column_name: str) -> Set
```

Iterates over raw rows and extract id values of relation columns by using
prefixed column name.

**Arguments**:

- `parent_model` (`Type[Model]`): ormar model class
- `column_name` (`str`): name of the relation column which is a key column

**Returns**:

`set`: set of ids of related model that should be extracted

<a name="queryset.prefetch_query.PrefetchQuery._extract_ids_from_preloaded_models"></a>
#### \_extract\_ids\_from\_preloaded\_models

```python
 | _extract_ids_from_preloaded_models(parent_model: Type["Model"], column_name: str) -> Set
```

Extracts relation ids from already populated models if they were included
in the original query before.

**Arguments**:

- `parent_model` (`Type["Model"]`): model from which related ids should be extracted
- `column_name` (`str`): name of the relation column which is a key column

**Returns**:

`set`: set of ids of related model that should be extracted

<a name="queryset.prefetch_query.PrefetchQuery._extract_required_ids"></a>
#### \_extract\_required\_ids

```python
 | _extract_required_ids(parent_model: Type["Model"], reverse: bool, related: str) -> Set
```

Delegates extraction of the fields to either get ids from raw sql response
or from already populated models.

**Arguments**:

- `parent_model` (`Type["Model"]`): model from which related ids should be extracted
- `reverse` (`bool`): flag if the relation is reverse
- `related` (`str`): name of the field with relation

**Returns**:

`set`: set of ids of related model that should be extracted

<a name="queryset.prefetch_query.PrefetchQuery._get_filter_for_prefetch"></a>
#### \_get\_filter\_for\_prefetch

```python
 | _get_filter_for_prefetch(parent_model: Type["Model"], target_model: Type["Model"], reverse: bool, related: str) -> List
```

Populates where clause with condition to return only models within the
set of extracted ids.

If there are no ids for relation the empty list is returned.

**Arguments**:

- `parent_model` (`Type["Model"]`): model from which related ids should be extracted
- `target_model` (`Type["Model"]`): model to which relation leads to
- `reverse` (`bool`): flag if the relation is reverse
- `related` (`str`): name of the field with relation

**Returns**:

`List[sqlalchemy.sql.elements.TextClause]`: 

<a name="queryset.prefetch_query.PrefetchQuery._populate_nested_related"></a>
#### \_populate\_nested\_related

```python
 | _populate_nested_related(model: "Model", prefetch_dict: Dict, orders_by: Dict) -> "Model"
```

Populates all related models children of parent model that are
included in prefetch query.

**Arguments**:

- `model` (`Model`): ormar model instance
- `prefetch_dict` (`Dict`): dictionary of models to prefetch
- `orders_by` (`Dict`): dictionary of order bys

**Returns**:

`Model`: model with children populated

<a name="queryset.prefetch_query.PrefetchQuery._prefetch_related_models"></a>
#### \_prefetch\_related\_models

```python
 | async _prefetch_related_models(models: Sequence["Model"], rows: List) -> Sequence["Model"]
```

Main method of the query.

Translates select nad prefetch list into dictionaries to avoid querying the
same related models multiple times.

Keeps the list of already extracted models.

Extracts the related models from the database and later populate all children
on each of the parent models from list.

**Arguments**:

- `models` (`List[Model]`): list of parent models from main query
- `rows` (`List[sqlalchemy.engine.result.RowProxy]`): raw response from sql query

**Returns**:

`List[Model]`: list of models with prefetch children populated

<a name="queryset.prefetch_query.PrefetchQuery._extract_related_models"></a>
#### \_extract\_related\_models

```python
 | async _extract_related_models(related: str, target_model: Type["Model"], prefetch_dict: Dict, select_dict: Dict, excludable: "ExcludableItems", orders_by: Dict) -> None
```

Constructs queries with required ids and extracts data with fields that should
be included/excluded.

Runs the queries against the database and populated dictionaries with ids and
with actual extracted children models.

Calls itself recurrently to extract deeper nested relations of related model.

**Arguments**:

- `related` (`str`): name of the relation
- `target_model` (`Type[Model]`): model to which relation leads to
- `prefetch_dict` (`Dict`): prefetch related list converted into dictionary
- `select_dict` (`Dict`): select related list converted into dictionary
- `fields` (`Union[Set[Any], Dict[Any, Any], None]`): fields to include
- `exclude_fields` (`Union[Set[Any], Dict[Any, Any], None]`): fields to exclude
- `orders_by` (`Dict`): dictionary of order bys clauses

**Returns**:

`None`: None

<a name="queryset.prefetch_query.PrefetchQuery._run_prefetch_query"></a>
#### \_run\_prefetch\_query

```python
 | async _run_prefetch_query(target_field: "BaseField", excludable: "ExcludableItems", filter_clauses: List, related_field_name: str) -> Tuple[str, str, List]
```

Actually runs the queries against the database and populates the raw response
for given related model.

Returns table prefix as it's later needed to eventually initialize the children
models.

**Arguments**:

- `target_field` (`"BaseField"`): ormar field with relation definition
- `filter_clauses` (`List[sqlalchemy.sql.elements.TextClause]`): list of clauses, actually one clause with ids of relation

**Returns**:

`Tuple[str, List]`: table prefix and raw rows from sql response

<a name="queryset.prefetch_query.PrefetchQuery._get_select_related_if_apply"></a>
#### \_get\_select\_related\_if\_apply

```python
 | @staticmethod
 | _get_select_related_if_apply(related: str, select_dict: Dict) -> Dict
```

Extract nested related of select_related dictionary to extract models nested
deeper on related model and already loaded in select related query.

**Arguments**:

- `related` (`str`): name of the relation
- `select_dict` (`Dict`): dictionary of select related models in main query

**Returns**:

`Dict`: dictionary with nested related of select related

<a name="queryset.prefetch_query.PrefetchQuery._update_already_loaded_rows"></a>
#### \_update\_already\_loaded\_rows

```python
 | _update_already_loaded_rows(target_field: "BaseField", prefetch_dict: Dict, orders_by: Dict) -> None
```

Updates models that are already loaded, usually children of children.

**Arguments**:

- `target_field` (`"BaseField"`): ormar field with relation definition
- `prefetch_dict` (`Dict`): dictionaries of related models to prefetch
- `orders_by` (`Dict`): dictionary of order by clauses by model

<a name="queryset.prefetch_query.PrefetchQuery._populate_rows"></a>
#### \_populate\_rows

```python
 | _populate_rows(rows: List, target_field: "ForeignKeyField", parent_model: Type["Model"], table_prefix: str, exclude_prefix: str, excludable: "ExcludableItems", prefetch_dict: Dict, orders_by: Dict) -> None
```

Instantiates children models extracted from given relation.

Populates them with their own nested children if they are included in prefetch
query.

Sets the initialized models and ids of them under corresponding keys in
already_extracted dictionary. Later those instances will be fetched by ids
and set on the parent model after sorting if needed.

**Arguments**:

- `excludable` (`ExcludableItems`): structure of fields to include and exclude
- `rows` (`List[sqlalchemy.engine.result.RowProxy]`): raw sql response from the prefetch query
- `target_field` (`"BaseField"`): field with relation definition from parent model
- `parent_model` (`Type[Model]`): model with relation definition
- `table_prefix` (`str`): prefix of the target table from current relation
- `prefetch_dict` (`Dict`): dictionaries of related models to prefetch
- `orders_by` (`Dict`): dictionary of order by clauses by model

