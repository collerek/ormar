<a name="queryset.join"></a>
# queryset.join

<a name="queryset.join.SqlJoin"></a>
## SqlJoin Objects

```python
class SqlJoin()
```

<a name="queryset.join.SqlJoin.alias_manager"></a>
#### alias\_manager

```python
 | @property
 | alias_manager() -> AliasManager
```

Shortcut for ormar's model AliasManager stored on Meta.

**Returns**:

`AliasManager`: alias manager from model's Meta

<a name="queryset.join.SqlJoin.to_table"></a>
#### to\_table

```python
 | @property
 | to_table() -> sqlalchemy.Table
```

Shortcut to table name of the next model

**Returns**:

`str`: name of the target table

<a name="queryset.join.SqlJoin._on_clause"></a>
#### \_on\_clause

```python
 | _on_clause(previous_alias: str, from_clause: str, to_clause: str) -> text
```

Receives aliases and names of both ends of the join and combines them
into one text clause used in joins.

**Arguments**:

- `previous_alias` (`str`): alias of previous table
- `from_clause` (`str`): from table name
- `to_clause` (`str`): to table name

**Returns**:

`sqlalchemy.text`: clause combining all strings

<a name="queryset.join.SqlJoin.build_join"></a>
#### build\_join

```python
 | build_join() -> Tuple[List, sqlalchemy.sql.select, List, OrderedDict]
```

Main external access point for building a join.
Splits the join definition, updates fields and exclude_fields if needed,
handles switching to through models for m2m relations, returns updated lists of
used_aliases and sort_orders.

**Returns**:

`Tuple[List[str], Join, List[TextClause], collections.OrderedDict]`: list of used aliases, select from, list of aliased columns, sort orders

<a name="queryset.join.SqlJoin._forward_join"></a>
#### \_forward\_join

```python
 | _forward_join() -> None
```

Process actual join.
Registers complex relation join on encountering of the duplicated alias.

<a name="queryset.join.SqlJoin._process_following_joins"></a>
#### \_process\_following\_joins

```python
 | _process_following_joins() -> None
```

Iterates through nested models to create subsequent joins.

<a name="queryset.join.SqlJoin._process_deeper_join"></a>
#### \_process\_deeper\_join

```python
 | _process_deeper_join(related_name: str, remainder: Any) -> None
```

Creates nested recurrent instance of SqlJoin for each nested join table,
updating needed return params here as a side effect.

Updated are:

* self.used_aliases,
* self.select_from,
* self.columns,
* self.sorted_orders,

**Arguments**:

- `related_name` (`str`): name of the relation to follow
- `remainder` (`Any`): deeper tables if there are more nested joins

<a name="queryset.join.SqlJoin._process_m2m_through_table"></a>
#### \_process\_m2m\_through\_table

```python
 | _process_m2m_through_table() -> None
```

Process Through table of the ManyToMany relation so that source table is
linked to the through table (one additional join)

Replaces needed parameters like:

* self.next_model,
* self.next_alias,
* self.relation_name,
* self.own_alias,
* self.target_field

To point to through model

<a name="queryset.join.SqlJoin._process_m2m_related_name_change"></a>
#### \_process\_m2m\_related\_name\_change

```python
 | _process_m2m_related_name_change(reverse: bool = False) -> str
```

Extracts relation name to link join through the Through model declared on
relation field.

Changes the same names in order_by queries if they are present.

**Arguments**:

- `reverse` (`bool`): flag if it's on_clause lookup - use reverse fields

**Returns**:

`str`: new relation name switched to through model field

<a name="queryset.join.SqlJoin._process_join"></a>
#### \_process\_join

```python
 | _process_join() -> None
```

Resolves to and from column names and table names.

Produces on_clause.

Performs actual join updating select_from parameter.

Adds aliases of required column to list of columns to include in query.

Updates the used aliases list directly.

Process order_by causes for non m2m relations.

<a name="queryset.join.SqlJoin._verify_allowed_order_field"></a>
#### \_verify\_allowed\_order\_field

```python
 | _verify_allowed_order_field(order_by: str) -> None
```

Verifies if proper field string is used.

**Arguments**:

- `order_by` (`str`): string with order by definition

<a name="queryset.join.SqlJoin._get_alias_and_model"></a>
#### \_get\_alias\_and\_model

```python
 | _get_alias_and_model(order_by: str) -> Tuple[str, Type["Model"]]
```

Returns proper model and alias to be applied in the clause.

**Arguments**:

- `order_by` (`str`): string with order by definition

**Returns**:

`Tuple[str, Type["Model"]]`: alias and model to be used in clause

<a name="queryset.join.SqlJoin._get_order_bys"></a>
#### \_get\_order\_bys

```python
 | _get_order_bys() -> None
```

Triggers construction of order bys if they are given.
Otherwise by default each table is sorted by a primary key column asc.

<a name="queryset.join.SqlJoin._get_to_and_from_keys"></a>
#### \_get\_to\_and\_from\_keys

```python
 | _get_to_and_from_keys() -> Tuple[str, str]
```

Based on the relation type, name of the relation and previous models and parts
stored in JoinParameters it resolves the current to and from keys, which are
different for ManyToMany relation, ForeignKey and reverse related of relations.

**Returns**:

`Tuple[str, str]`: to key and from key

