<a name="queryset.reverse_alias_resolver"></a>
# queryset.reverse\_alias\_resolver

<a name="queryset.reverse_alias_resolver.ReverseAliasResolver"></a>
## ReverseAliasResolver Objects

```python
class ReverseAliasResolver()
```

Class is used to reverse resolve table aliases into relation strings
to parse raw data columns and replace table prefixes with full relation string

<a name="queryset.reverse_alias_resolver.ReverseAliasResolver.resolve_columns"></a>
#### resolve\_columns

```python
 | resolve_columns(columns_names: List[str]) -> Dict
```

Takes raw query prefixed column and resolves the prefixes to
relation strings (relation names connected with dunders).

**Arguments**:

- `columns_names` (`List[str]`): list of column names with prefixes from query

**Returns**:

`Union[None, Dict[str, str]]`: dictionary of prefix: resolved names

<a name="queryset.reverse_alias_resolver.ReverseAliasResolver._resolve_column_with_prefix"></a>
#### \_resolve\_column\_with\_prefix

```python
 | _resolve_column_with_prefix(column_name: str, prefix: str) -> None
```

Takes the prefixed column, checks if field should be excluded, and if not
it proceeds to replace prefix of a table with full relation string.

Sample: translates: "xsd12df_name" -> into: "posts__user__name"

**Arguments**:

- `column_name` (`str`): prefixed name of the column
- `prefix` (`str`): extracted prefix

<a name="queryset.reverse_alias_resolver.ReverseAliasResolver._check_if_field_is_excluded"></a>
#### \_check\_if\_field\_is\_excluded

```python
 | _check_if_field_is_excluded(prefix: str, field: "ForeignKeyField", is_through: bool) -> bool
```

Checks if given relation is excluded in current query.

Note that in contrary to other queryset methods here you can exclude the
in-between models but keep the end columns, which does not make sense
when parsing the raw data into models.

So in relation category -> category_x_post -> post -> user you can exclude
category_x_post and post models but can keep the user one. (in ormar model
context that is not possible as if you would exclude through and post model
there would be no way to reach user model).

Exclusions happen on a model before the current one, so we need to move back
in chain of model by one or by two (m2m relations have through model in between)

**Arguments**:

- `prefix` (`str`): table alias
- `field` (`ForeignKeyField`): field with relation
- `is_through` (`bool`): flag if current table is a through table

**Returns**:

`bool`: result of the check

<a name="queryset.reverse_alias_resolver.ReverseAliasResolver._get_previous_excludable"></a>
#### \_get\_previous\_excludable

```python
 | _get_previous_excludable(prefix: str, field: "ForeignKeyField", shift: int = 1) -> "Excludable"
```

Returns excludable related to model previous in chain of models.
Used to check if current model should be excluded.

**Arguments**:

- `prefix` (`str`): prefix of a current table
- `field` (`ForeignKeyField`): field with relation
- `shift` (`int`): how many model back to go - for m2m it's 2 due to through models

**Returns**:

`Excludable`: excludable for previous model

<a name="queryset.reverse_alias_resolver.ReverseAliasResolver._create_prefixes_map"></a>
#### \_create\_prefixes\_map

```python
 | _create_prefixes_map() -> None
```

Creates a map of alias manager aliases keys to relation strings.
I.e in alias manager you can have alias user_roles: xas12ad

This method will create entry user_roles: roles, where roles is a name of
relation on user model.

Will also keep the relation field in separate dictionary so we can later
extract field names and owner models.

<a name="queryset.reverse_alias_resolver.ReverseAliasResolver._handle_through_fields_and_prefix"></a>
#### \_handle\_through\_fields\_and\_prefix

```python
 | _handle_through_fields_and_prefix(model_cls: Type["Model"], field: "ForeignKeyField", previous_related_str: str, relation: str) -> str
```

Registers through models for m2m relations and switches prefix for
the one linking from through model to target model.

For other relations returns current model name + relation name as prefix.
Nested relations are a chain of relation names with __ in between.

**Arguments**:

- `model_cls` (`Type["Model"]`): model of current relation
- `field` (`ForeignKeyField`): field with relation
- `previous_related_str` (`str`): concatenated chain linked with "__"
- `relation` (`str`): name of the current relation in chain

**Returns**:

`str`: name of prefix to populate

