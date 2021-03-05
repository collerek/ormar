<a name="relations.alias_manager"></a>
# relations.alias\_manager

<a name="relations.alias_manager.get_table_alias"></a>
#### get\_table\_alias

```python
get_table_alias() -> str
```

Creates a random string that is used to alias tables in joins.
It's necessary that each relation has it's own aliases cause you can link
to the same target tables from multiple fields on one model as well as from
multiple different models in one join.

**Returns**:

`(str)`: randomly generated alias

<a name="relations.alias_manager.AliasManager"></a>
## AliasManager Objects

```python
class AliasManager()
```

Keep all aliases of relations between different tables.
One global instance is shared between all models.

<a name="relations.alias_manager.AliasManager.prefixed_columns"></a>
#### prefixed\_columns

```python
 | @staticmethod
 | prefixed_columns(alias: str, table: sqlalchemy.Table, fields: List = None) -> List[text]
```

Creates a list of aliases sqlalchemy text clauses from
string alias and sqlalchemy.Table.

Optional list of fields to include can be passed to extract only those columns.
List has to have sqlalchemy names of columns (ormar aliases) not the ormar ones.

**Arguments**:

- `alias (str)`: alias of given table
- `table (sqlalchemy.Table)`: table from which fields should be aliased
- `fields (Optional[List[str]])`: fields to include

**Returns**:

`(List[text])`: list of sqlalchemy text clauses with "column name as aliased name"

<a name="relations.alias_manager.AliasManager.prefixed_table_name"></a>
#### prefixed\_table\_name

```python
 | @staticmethod
 | prefixed_table_name(alias: str, name: str) -> text
```

Creates text clause with table name with aliased name.

**Arguments**:

- `alias (str)`: alias of given table
- `name (str)`: table name

**Returns**:

`(sqlalchemy text clause)`: sqlalchemy text clause as "table_name aliased_name"

<a name="relations.alias_manager.AliasManager.add_relation_type"></a>
#### add\_relation\_type

```python
 | add_relation_type(source_model: Type["Model"], relation_name: str, reverse_name: str = None) -> None
```

Registers the relations defined in ormar models.
Given the relation it registers also the reverse side of this relation.

Used by both ForeignKey and ManyToMany relations.

Each relation is registered as Model name and relation name.
Each alias registered has to be unique.

Aliases are used to construct joins to assure proper links between tables.
That way you can link to the same target tables from multiple fields
on one model as well as from multiple different models in one join.

**Arguments**:

- `source_model (source Model)`: model with relation defined
- `relation_name (str)`: name of the relation to define
- `reverse_name (Optional[str])`: name of related_name fo given relation for m2m relations

**Returns**:

`(None)`: none

<a name="relations.alias_manager.AliasManager.add_alias"></a>
#### add\_alias

```python
 | add_alias(alias_key: str) -> str
```

Adds alias to the dictionary of aliases under given key.

**Arguments**:

- `alias_key (str)`: key of relation to generate alias for

**Returns**:

`(str)`: generated alias

<a name="relations.alias_manager.AliasManager.resolve_relation_alias"></a>
#### resolve\_relation\_alias

```python
 | resolve_relation_alias(from_model: Union[Type["Model"], Type["ModelRow"]], relation_name: str) -> str
```

Given model and relation name returns the alias for this relation.

**Arguments**:

- `from_model (source Model)`: model with relation defined
- `relation_name (str)`: name of the relation field

**Returns**:

`(str)`: alias of the relation

<a name="relations.alias_manager.AliasManager.resolve_relation_alias_after_complex"></a>
#### resolve\_relation\_alias\_after\_complex

```python
 | resolve_relation_alias_after_complex(source_model: Union[Type["Model"], Type["ModelRow"]], relation_str: str, relation_field: Type["ForeignKeyField"]) -> str
```

Given source model and relation string returns the alias for this complex
relation if it exists, otherwise fallback to normal relation from a relation
field definition.

**Arguments**:

- `relation_field (Type["ForeignKeyField"])`: field with direct relation definition
- `source_model (source Model)`: model with query starts
- `relation_str (str)`: string with relation joins defined

**Returns**:

`(str)`: alias of the relation

