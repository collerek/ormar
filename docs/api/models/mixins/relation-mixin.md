<a name="models.mixins.relation_mixin"></a>
# models.mixins.relation\_mixin

<a name="models.mixins.relation_mixin.RelationMixin"></a>
## RelationMixin Objects

```python
class RelationMixin()
```

Used to return relation fields/names etc. from given model

<a name="models.mixins.relation_mixin.RelationMixin.extract_db_own_fields"></a>
#### extract\_db\_own\_fields

```python
 | @classmethod
 | extract_db_own_fields(cls) -> Set
```

Returns only fields that are stored in the own database table, exclude all
related fields.

**Returns**:

`Set`: set of model fields with relation fields excluded

<a name="models.mixins.relation_mixin.RelationMixin.extract_related_fields"></a>
#### extract\_related\_fields

```python
 | @classmethod
 | extract_related_fields(cls) -> List["ForeignKeyField"]
```

Returns List of ormar Fields for all relations declared on a model.
List is cached in cls._related_fields for quicker access.

**Returns**:

`List`: list of related fields

<a name="models.mixins.relation_mixin.RelationMixin.extract_through_names"></a>
#### extract\_through\_names

```python
 | @classmethod
 | extract_through_names(cls) -> Set[str]
```

Extracts related fields through names which are shortcuts to through models.

**Returns**:

`Set`: set of related through fields names

<a name="models.mixins.relation_mixin.RelationMixin.extract_related_names"></a>
#### extract\_related\_names

```python
 | @classmethod
 | extract_related_names(cls) -> Set[str]
```

Returns List of fields names for all relations declared on a model.
List is cached in cls._related_names for quicker access.

**Returns**:

`Set`: set of related fields names

<a name="models.mixins.relation_mixin.RelationMixin._extract_db_related_names"></a>
#### \_extract\_db\_related\_names

```python
 | @classmethod
 | _extract_db_related_names(cls) -> Set
```

Returns only fields that are stored in the own database table, exclude
related fields that are not stored as foreign keys on given model.

**Returns**:

`Set`: set of model fields with non fk relation fields excluded

<a name="models.mixins.relation_mixin.RelationMixin._iterate_related_models"></a>
#### \_iterate\_related\_models

```python
 | @classmethod
 | _iterate_related_models(cls, node_list: NodeList = None, source_relation: str = None) -> List[str]
```

Iterates related models recursively to extract relation strings of
nested not visited models.

**Returns**:

`List[str]`: list of relation strings to be passed to select_related

<a name="models.mixins.relation_mixin.RelationMixin._get_final_relations"></a>
#### \_get\_final\_relations

```python
 | @staticmethod
 | _get_final_relations(processed_relations: List, source_relation: Optional[str]) -> List[str]
```

Helper method to prefix nested relation strings with current source relation

**Arguments**:

- `processed_relations` (`List[str]`): list of already processed relation str
- `source_relation` (`str`): name of the current relation

**Returns**:

`List[str]`: list of relation strings to be passed to select_related

