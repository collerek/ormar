<a name="queryset.clause"></a>
# queryset.clause

<a name="queryset.clause.QueryClause"></a>
## QueryClause Objects

```python
class QueryClause()
```

Constructs FilterActions from strings passed as arguments

<a name="queryset.clause.QueryClause.prepare_filter"></a>
#### prepare\_filter

```python
 | prepare_filter(**kwargs: Any) -> Tuple[List[FilterAction], List[str]]
```

Main external access point that processes the clauses into sqlalchemy text
clauses and updates select_related list with implicit related tables
mentioned in select_related strings but not included in select_related.

**Arguments**:

- `kwargs (Any)`: key, value pair with column names and values

**Returns**:

`(Tuple[List[sqlalchemy.sql.elements.TextClause], List[str]])`: Tuple with list of where clauses and updated select_related list

<a name="queryset.clause.QueryClause._populate_filter_clauses"></a>
#### \_populate\_filter\_clauses

```python
 | _populate_filter_clauses(**kwargs: Any) -> Tuple[List[FilterAction], List[str]]
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

