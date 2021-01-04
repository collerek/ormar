<a name="queryset.clause"></a>
# queryset.clause

<a name="queryset.clause.FILTER_OPERATORS"></a>
#### FILTER\_OPERATORS

<a name="queryset.clause.ESCAPE_CHARACTERS"></a>
#### ESCAPE\_CHARACTERS

<a name="queryset.clause.QueryClause"></a>
## QueryClause Objects

```python
class QueryClause()
```

Constructs where clauses from strings passed as arguments

<a name="queryset.clause.QueryClause.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(model_cls: Type["Model"], filter_clauses: List, select_related: List) -> None
```

<a name="queryset.clause.QueryClause.filter"></a>
#### filter

```python
 | filter(**kwargs: Any) -> Tuple[List[sqlalchemy.sql.expression.TextClause], List[str]]
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
 | _populate_filter_clauses(**kwargs: Any) -> Tuple[List[sqlalchemy.sql.expression.TextClause], List[str]]
```

Iterates all clauses and extracts used operator and field from related
models if needed. Based on the chain of related names the target table
is determined and the final clause is escaped if needed and compiled.

**Arguments**:

- `kwargs (Any)`: key, value pair with column names and values

**Returns**:

`(Tuple[List[sqlalchemy.sql.elements.TextClause], List[str]])`: Tuple with list of where clauses and updated select_related list

<a name="queryset.clause.QueryClause._process_column_clause_for_operator_and_value"></a>
#### \_process\_column\_clause\_for\_operator\_and\_value

```python
 | _process_column_clause_for_operator_and_value(value: Any, op: str, column: sqlalchemy.Column, table: sqlalchemy.Table, table_prefix: str) -> sqlalchemy.sql.expression.TextClause
```

Escapes characters if it's required.
Substitutes values of the models if value is a ormar Model with its pk value.
Compiles the clause.

**Arguments**:

- `value (Any)`: value of the filter
- `op (str)`: filter operator
- `column (sqlalchemy.sql.schema.Column)`: column on which filter should be applied
- `table (sqlalchemy.sql.schema.Table)`: table on which filter should be applied
- `table_prefix (str)`: prefix from AliasManager

**Returns**:

`(sqlalchemy.sql.elements.TextClause)`: complied and escaped clause

<a name="queryset.clause.QueryClause._determine_filter_target_table"></a>
#### \_determine\_filter\_target\_table

```python
 | _determine_filter_target_table(related_parts: List[str], select_related: List[str]) -> Tuple[List[str], str, Type["Model"]]
```

Adds related strings to select_related list otherwise the clause would fail as
the required columns would not be present. That means that select_related
list is filled with missing values present in filters.

Walks the relation to retrieve the actual model on which the clause should be
constructed, extracts alias based on last relation leading to target model.

**Arguments**:

- `related_parts (List[str])`: list of split parts of related string
- `select_related (List[str])`: list of related models

**Returns**:

`(Tuple[List[str], str, Type[Model]])`: list of related models, table_prefix, final model class

<a name="queryset.clause.QueryClause._compile_clause"></a>
#### \_compile\_clause

```python
 | _compile_clause(clause: sqlalchemy.sql.expression.BinaryExpression, column: sqlalchemy.Column, table: sqlalchemy.Table, table_prefix: str, modifiers: Dict) -> sqlalchemy.sql.expression.TextClause
```

Compiles the clause to str using appropriate database dialect, replace columns
names with aliased names and converts it back to TextClause.

**Arguments**:

- `clause (sqlalchemy.sql.elements.BinaryExpression)`: original not compiled clause
- `column (sqlalchemy.sql.schema.Column)`: column on which filter should be applied
- `table (sqlalchemy.sql.schema.Table)`: table on which filter should be applied
- `table_prefix (str)`: prefix from AliasManager
- `modifiers (Dict[str, NoneType])`: sqlalchemy modifiers - used only to escape chars here

**Returns**:

`(sqlalchemy.sql.elements.TextClause)`: compiled and escaped clause

<a name="queryset.clause.QueryClause._escape_characters_in_clause"></a>
#### \_escape\_characters\_in\_clause

```python
 | @staticmethod
 | _escape_characters_in_clause(op: str, value: Any) -> Tuple[Any, bool]
```

Escapes the special characters ["%", "_"] if needed.
Adds `%` for `like` queries.

**Raises**:

- `QueryDefinitionError`: if contains or icontains is used with
ormar model instance

**Arguments**:

- `op (str)`: operator used in query
- `value (Any)`: value of the filter

**Returns**:

`(Tuple[Any, bool])`: escaped value and flag if escaping is needed

<a name="queryset.clause.QueryClause._extract_operator_field_and_related"></a>
#### \_extract\_operator\_field\_and\_related

```python
 | @staticmethod
 | _extract_operator_field_and_related(parts: List[str]) -> Tuple[str, str, Optional[List]]
```

Splits filter query key and extracts required parts.

**Arguments**:

- `parts (List[str])`: split filter query key

**Returns**:

`(Tuple[str, str, Optional[List]])`: operator, field_name, list of related parts

