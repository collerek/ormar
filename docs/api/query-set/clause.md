<a name="queryset.clause"></a>
# queryset.clause

<a name="queryset.clause.FilterGroup"></a>
## FilterGroup Objects

```python
class FilterGroup()
```

Filter groups are used in complex queries condition to group and and or
clauses in where condition

<a name="queryset.clause.FilterGroup.resolve"></a>
#### resolve

```python
 | resolve(model_cls: Type["Model"], select_related: List = None, filter_clauses: List = None) -> Tuple[List[FilterAction], List[str]]
```

Resolves the FilterGroups actions to use proper target model, replace
complex relation prefixes if needed and nested groups also resolved.

**Arguments**:

- `model_cls (Type["Model"])`: model from which the query is run
- `select_related (List[str])`: list of models to join
- `filter_clauses (List[FilterAction])`: list of filter conditions

**Returns**:

`(Tuple[List[FilterAction], List[str]])`: list of filter conditions and select_related list

<a name="queryset.clause.FilterGroup._iter"></a>
#### \_iter

```python
 | _iter() -> Generator
```

Iterates all actions in a tree

**Returns**:

`(Generator)`: generator yielding from own actions and nested groups

<a name="queryset.clause.FilterGroup._get_text_clauses"></a>
#### \_get\_text\_clauses

```python
 | _get_text_clauses() -> List[sqlalchemy.sql.expression.TextClause]
```

Helper to return list of text queries from actions and nested groups

**Returns**:

`(List[sqlalchemy.sql.elements.TextClause])`: list of text queries from actions and nested groups

<a name="queryset.clause.FilterGroup.get_text_clause"></a>
#### get\_text\_clause

```python
 | get_text_clause() -> sqlalchemy.sql.expression.TextClause
```

Returns all own actions and nested groups conditions compiled and joined
inside parentheses.
Escapes characters if it's required.
Substitutes values of the models if value is a ormar Model with its pk value.
Compiles the clause.

**Returns**:

`(sqlalchemy.sql.elements.TextClause)`: complied and escaped clause

<a name="queryset.clause.or_"></a>
#### or\_

```python
or_(*args: FilterGroup, **kwargs: Any) -> FilterGroup
```

Construct or filter from nested groups and keyword arguments

**Arguments**:

- `args (Tuple[FilterGroup])`: nested filter groups
- `kwargs (Any)`: fields names and proper value types

**Returns**:

`(ormar.queryset.clause.FilterGroup)`: FilterGroup ready to be resolved

<a name="queryset.clause.and_"></a>
#### and\_

```python
and_(*args: FilterGroup, **kwargs: Any) -> FilterGroup
```

Construct and filter from nested groups and keyword arguments

**Arguments**:

- `args (Tuple[FilterGroup])`: nested filter groups
- `kwargs (Any)`: fields names and proper value types

**Returns**:

`(ormar.queryset.clause.FilterGroup)`: FilterGroup ready to be resolved

<a name="queryset.clause.QueryClause"></a>
## QueryClause Objects

```python
class QueryClause()
```

Constructs FilterActions from strings passed as arguments

<a name="queryset.clause.QueryClause.prepare_filter"></a>
#### prepare\_filter

```python
 | prepare_filter(_own_only: bool = False, **kwargs: Any) -> Tuple[List[FilterAction], List[str]]
```

Main external access point that processes the clauses into sqlalchemy text
clauses and updates select_related list with implicit related tables
mentioned in select_related strings but not included in select_related.

**Arguments**:

- `_own_only ()`: 
- `kwargs (Any)`: key, value pair with column names and values

**Returns**:

`(Tuple[List[sqlalchemy.sql.elements.TextClause], List[str]])`: Tuple with list of where clauses and updated select_related list

<a name="queryset.clause.QueryClause._populate_filter_clauses"></a>
#### \_populate\_filter\_clauses

```python
 | _populate_filter_clauses(_own_only: bool, **kwargs: Any) -> Tuple[List[FilterAction], List[str]]
```

Iterates all clauses and extracts used operator and field from related
models if needed. Based on the chain of related names the target table
is determined and the final clause is escaped if needed and compiled.

**Arguments**:

- `kwargs (Any)`: key, value pair with column names and values

**Returns**:

`(Tuple[List[sqlalchemy.sql.elements.TextClause], List[str]])`: Tuple with list of where clauses and updated select_related list

<a name="queryset.clause.QueryClause._register_complex_duplicates"></a>
#### \_register\_complex\_duplicates

```python
 | _register_complex_duplicates(select_related: List[str]) -> None
```

Checks if duplicate aliases are presented which can happen in self relation
or when two joins end with the same pair of models.

If there are duplicates, the all duplicated joins are registered as source
model and whole relation key (not just last relation name).

**Arguments**:

- `select_related (List[str])`: list of relation strings

**Returns**:

`(None)`: None

<a name="queryset.clause.QueryClause._parse_related_prefixes"></a>
#### \_parse\_related\_prefixes

```python
 | _parse_related_prefixes(select_related: List[str]) -> List[Prefix]
```

Walks all relation strings and parses the target models and prefixes.

**Arguments**:

- `select_related (List[str])`: list of relation strings

**Returns**:

`(List[Prefix])`: list of parsed prefixes

<a name="queryset.clause.QueryClause._switch_filter_action_prefixes"></a>
#### \_switch\_filter\_action\_prefixes

```python
 | _switch_filter_action_prefixes(filter_clauses: List[FilterAction]) -> List[FilterAction]
```

Substitutes aliases for filter action if the complex key (whole relation str) is
present in alias_manager.

**Arguments**:

- `filter_clauses (List[FilterAction])`: raw list of actions

**Returns**:

`(List[FilterAction])`: list of actions with aliases changed if needed

<a name="queryset.clause.QueryClause._verify_prefix_and_switch"></a>
#### \_verify\_prefix\_and\_switch

```python
 | _verify_prefix_and_switch(action: "FilterAction") -> None
```

Helper to switch prefix to complex relation one if required

**Arguments**:

- `action (ormar.queryset.actions.filter_action.FilterAction)`: action to switch prefix in

