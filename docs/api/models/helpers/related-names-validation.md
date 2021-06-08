<a name="models.helpers.related_names_validation"></a>
# models.helpers.related\_names\_validation

<a name="models.helpers.related_names_validation.validate_related_names_in_relations"></a>
#### validate\_related\_names\_in\_relations

```python
validate_related_names_in_relations(model_fields: Dict, new_model: Type["Model"]) -> None
```

Performs a validation of relation_names in relation fields.
If multiple fields are leading to the same related model
only one can have empty related_name param
(populated by default as model.name.lower()+'s').
Also related_names have to be unique for given related model.

**Raises**:

- `ModelDefinitionError`: if validation of related_names fail

**Arguments**:

- `model_fields` (`Dict[str, ormar.Field]`): dictionary of declared ormar model fields
- `new_model` (`Model class`): 

