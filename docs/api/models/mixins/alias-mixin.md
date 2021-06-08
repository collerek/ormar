<a name="models.mixins.alias_mixin"></a>
# models.mixins.alias\_mixin

<a name="models.mixins.alias_mixin.AliasMixin"></a>
## AliasMixin Objects

```python
class AliasMixin()
```

Used to translate field names into database column names.

<a name="models.mixins.alias_mixin.AliasMixin.get_column_alias"></a>
#### get\_column\_alias

```python
 | @classmethod
 | get_column_alias(cls, field_name: str) -> str
```

Returns db alias (column name in db) for given ormar field.
For fields without alias field name is returned.

**Arguments**:

- `field_name` (`str`): name of the field to get alias from

**Returns**:

`str`: alias (db name) if set, otherwise passed name

<a name="models.mixins.alias_mixin.AliasMixin.get_column_name_from_alias"></a>
#### get\_column\_name\_from\_alias

```python
 | @classmethod
 | get_column_name_from_alias(cls, alias: str) -> str
```

Returns ormar field name for given db alias (column name in db).
If field do not have alias it's returned as is.

**Arguments**:

- `alias` (`str`): 

**Returns**:

`str`: field name if set, otherwise passed alias (db name)

<a name="models.mixins.alias_mixin.AliasMixin.translate_columns_to_aliases"></a>
#### translate\_columns\_to\_aliases

```python
 | @classmethod
 | translate_columns_to_aliases(cls, new_kwargs: Dict) -> Dict
```

Translates dictionary of model fields changing field names into aliases.
If field has no alias the field name remains intact.
Only fields present in the dictionary are translated.

**Arguments**:

- `new_kwargs` (`Dict`): dict with fields names and their values

**Returns**:

`Dict`: dict with aliases and their values

<a name="models.mixins.alias_mixin.AliasMixin.translate_aliases_to_columns"></a>
#### translate\_aliases\_to\_columns

```python
 | @classmethod
 | translate_aliases_to_columns(cls, new_kwargs: Dict) -> Dict
```

Translates dictionary of model fields changing aliases into field names.
If field has no alias the alias is already a field name.
Only fields present in the dictionary are translated.

**Arguments**:

- `new_kwargs` (`Dict`): dict with aliases and their values

**Returns**:

`Dict`: dict with fields names and their values

