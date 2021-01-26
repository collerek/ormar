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

`(AliasManager)`: alias manager from model's Meta

<a name="queryset.join.SqlJoin.on_clause"></a>
#### on\_clause

```python
 | on_clause(previous_alias: str, from_clause: str, to_clause: str) -> text
```

Receives aliases and names of both ends of the join and combines them
into one text clause used in joins.

**Arguments**:

- `previous_alias (str)`: alias of previous table
- `from_clause (str)`: from table name
- `to_clause (str)`: to table name

**Returns**:

`(sqlalchemy.text)`: clause combining all strings

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

`(Tuple[List[str], Join, List[TextClause], collections.OrderedDict])`: list of used aliases, select from, list of aliased columns, sort orders

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

- `related_name (str)`: name of the relation to follow
- `remainder (Any)`: deeper tables if there are more nested joins

<a name="queryset.join.SqlJoin.process_m2m_through_table"></a>
#### process\_m2m\_through\_table

```python
 | process_m2m_through_table() -> None
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

<a name="queryset.join.SqlJoin.process_m2m_related_name_change"></a>
#### process\_m2m\_related\_name\_change

```python
 | process_m2m_related_name_change(reverse: bool = False) -> str
```

Extracts relation name to link join through the Through model declared on
relation field.

Changes the same names in order_by queries if they are present.

**Arguments**:

- `reverse (bool)`: flag if it's on_clause lookup - use reverse fields

**Returns**:

`(str)`: new relation name switched to through model field

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

<a name="queryset.join.SqlJoin._replace_many_to_many_order_by_columns"></a>
#### \_replace\_many\_to\_many\_order\_by\_columns

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
 | set_aliased_order_by(condition: List[str], to_table: str) -> None
```

Substitute hyphens ('-') with descending order.
Construct actual sqlalchemy text clause using aliased table and column name.

**Arguments**:

- `condition (List[str])`: list of parts of a current condition split by '__'
- `to_table (sqlalchemy.sql.elements.quoted_name)`: target table

<a name="queryset.join.SqlJoin.get_order_bys"></a>
#### get\_order\_bys

```python
 | get_order_bys(to_table: str, pkname_alias: str) -> None
```

Triggers construction of order bys if they are given.
Otherwise by default each table is sorted by a primary key column asc.

**Arguments**:

- `to_table (sqlalchemy.sql.elements.quoted_name)`: target table
- `pkname_alias (str)`: alias of the primary key column

<a name="queryset.join.SqlJoin.get_to_and_from_keys"></a>
#### get\_to\_and\_from\_keys

```python
 | get_to_and_from_keys() -> Tuple[str, str]
```

Based on the relation type, name of the relation and previous models and parts
stored in JoinParameters it resolves the current to and from keys, which are
different for ManyToMany relation, ForeignKey and reverse related of relations.

**Returns**:

`(Tuple[str, str])`: to key and from key

