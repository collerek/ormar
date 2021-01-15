<a name="queryset.join"></a>
# queryset.join

<a name="queryset.join.JoinParameters"></a>
## JoinParameters Objects

```python
class JoinParameters(NamedTuple)
```

Named tuple that holds set of parameters passed during join construction.

<a name="queryset.join.SqlJoin"></a>
## SqlJoin Objects

```python
class SqlJoin()
```

<a name="queryset.join.SqlJoin.alias_manager"></a>
#### alias\_manager

```python
 | @staticmethod
 | alias_manager(model_cls: Type["Model"]) -> AliasManager
```

Shortcut for ormars model AliasManager stored on Meta.

**Arguments**:

- `model_cls (Type[Model])`: ormar Model class

**Returns**:

`(AliasManager)`: alias manager from model's Meta

<a name="queryset.join.SqlJoin.on_clause"></a>
#### on\_clause

```python
 | @staticmethod
 | on_clause(previous_alias: str, alias: str, from_clause: str, to_clause: str) -> text
```

Receives aliases and names of both ends of the join and combines them
into one text clause used in joins.

**Arguments**:

- `previous_alias (str)`: alias of previous table
- `alias (str)`: alias of current table
- `from_clause (str)`: from table name
- `to_clause (str)`: to table name

**Returns**:

`(sqlalchemy.text)`: clause combining all strings

<a name="queryset.join.SqlJoin.update_inclusions"></a>
#### update\_inclusions

```python
 | @staticmethod
 | update_inclusions(model_cls: Type["Model"], fields: Optional[Union[Set, Dict]], exclude_fields: Optional[Union[Set, Dict]], nested_name: str) -> Tuple[Optional[Union[Dict, Set]], Optional[Union[Dict, Set]]]
```

Extract nested fields and exclude_fields if applicable.

**Arguments**:

- `model_cls (Type["Model"])`: ormar model class
- `fields (Optional[Union[Set, Dict]])`: fields to include
- `exclude_fields (Optional[Union[Set, Dict]])`: fields to exclude
- `nested_name (str)`: name of the nested field

**Returns**:

`(Tuple[Optional[Union[Dict, Set]], Optional[Union[Dict, Set]]])`: updated exclude and include fields from nested objects

<a name="queryset.join.SqlJoin.build_join"></a>
#### build\_join

```python
 | build_join(item: str, join_parameters: JoinParameters) -> Tuple[List, sqlalchemy.sql.select, List, OrderedDict]
```

Main external access point for building a join.
Splits the join definition, updates fields and exclude_fields if needed,
handles switching to through models for m2m relations, returns updated lists of
used_aliases and sort_orders.

**Arguments**:

- `item (str)`: string with join definition
- `join_parameters (JoinParameters)`: parameters from previous/ current join

**Returns**:

`(Tuple[List[str], Join, List[TextClause], collections.OrderedDict])`: list of used aliases, select from, list of aliased columns, sort orders

<a name="queryset.join.SqlJoin._build_join_parameters"></a>
#### \_build\_join\_parameters

```python
 | _build_join_parameters(part: str, join_params: JoinParameters, fields: Optional[Union[Set, Dict]], exclude_fields: Optional[Union[Set, Dict]], is_multi: bool = False) -> JoinParameters
```

Updates used_aliases to not join multiple times to the same table.
Updates join parameters with new values.

**Arguments**:

- `part (str)`: part of the join str definition
- `join_params (JoinParameters)`: parameters from previous/ current join
- `fields (Optional[Union[Set, Dict]])`: fields to include
- `exclude_fields (Optional[Union[Set, Dict]])`: fields to exclude
- `is_multi (bool)`: flag if the relation is m2m

**Returns**:

`(ormar.queryset.join.JoinParameters)`: updated join parameters

<a name="queryset.join.SqlJoin._process_join"></a>
#### \_process\_join

```python
 | _process_join(join_params: JoinParameters, is_multi: bool, model_cls: Type["Model"], part: str, alias: str, fields: Optional[Union[Set, Dict]], exclude_fields: Optional[Union[Set, Dict]]) -> None
```

Resolves to and from column names and table names.

Produces on_clause.

Performs actual join updating select_from parameter.

Adds aliases of required column to list of columns to include in query.

Updates the used aliases list directly.

Process order_by causes for non m2m relations.

**Arguments**:

- `join_params (JoinParameters)`: parameters from previous/ current join
- `is_multi (bool)`: flag if it's m2m relation
- `model_cls (ormar.models.metaclass.ModelMetaclass)`: 
- `part (str)`: name of the field used in join
- `alias (str)`: alias of the current join
- `fields (Optional[Union[Set, Dict]])`: fields to include
- `exclude_fields (Optional[Union[Set, Dict]])`: fields to exclude

<a name="queryset.join.SqlJoin._replace_many_to_many_order_by_columns"></a>
#### \_switch\_many\_to\_many\_order\_columns

```python
 | _replace_many_to_many_order_by_columns(part: str, new_part: str) -> None
```

Substitutes the name of the relation with actual model name in m2m order bys.

**Arguments**:

- `part (str)`: name of the field with relation
- `new_part (str)`: name of the target model

<a name="queryset.join.SqlJoin._check_if_condition_apply"></a>
#### \_check\_if\_condition\_apply

```python
 | @staticmethod
 | _check_if_condition_apply(condition: List, part: str) -> bool
```

Checks filter conditions to find if they apply to current join.

**Arguments**:

- `condition (List[str])`: list of parts of condition split by '__'
- `part (str)`: name of the current relation join.

**Returns**:

`(bool)`: result of the check

<a name="queryset.join.SqlJoin.set_aliased_order_by"></a>
#### set\_aliased\_order\_by

```python
 | set_aliased_order_by(condition: List[str], alias: str, to_table: str, model_cls: Type["Model"]) -> None
```

Substitute hyphens ('-') with descending order.
Construct actual sqlalchemy text clause using aliased table and column name.

**Arguments**:

- `condition (List[str])`: list of parts of a current condition split by '__'
- `alias (str)`: alias of the table in current join
- `to_table (sqlalchemy.sql.elements.quoted_name)`: target table
- `model_cls (ormar.models.metaclass.ModelMetaclass)`: ormar model class

<a name="queryset.join.SqlJoin.get_order_bys"></a>
#### get\_order\_bys

```python
 | get_order_bys(alias: str, to_table: str, pkname_alias: str, part: str, model_cls: Type["Model"]) -> None
```

Triggers construction of order bys if they are given.
Otherwise by default each table is sorted by a primary key column asc.

**Arguments**:

- `alias (str)`: alias of current table in join
- `to_table (sqlalchemy.sql.elements.quoted_name)`: target table
- `pkname_alias (str)`: alias of the primary key column
- `part (str)`: name of the current relation join
- `model_cls (Type[Model])`: ormar model class

<a name="queryset.join.SqlJoin.get_to_and_from_keys"></a>
#### get\_to\_and\_from\_keys

```python
 | @staticmethod
 | get_to_and_from_keys(join_params: JoinParameters, is_multi: bool, model_cls: Type["Model"], part: str) -> Tuple[str, str]
```

Based on the relation type, name of the relation and previous models and parts
stored in JoinParameters it resolves the current to and from keys, which are
different for ManyToMany relation, ForeignKey and reverse part of relations.

**Arguments**:

- `join_params (JoinParameters)`: parameters from previous/ current join
- `is_multi (bool)`: flag if the relation is of m2m type
- `model_cls (Type[Model])`: ormar model class
- `part (str)`: name of the current relation join

**Returns**:

`(Tuple[str, str])`: to key and from key

