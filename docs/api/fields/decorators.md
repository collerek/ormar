<a name="decorators.property_field"></a>
# decorators.property\_field

<a name="decorators.property_field.property_field"></a>
#### property\_field

```python
property_field(func: Callable) -> Union[property, Callable]
```

Decorator to set a property like function on Model to be exposed
as field in dict() and fastapi response.
Although you can decorate a @property field like this and this will work,
mypy validation will complain about this.
Note that "fields" exposed like this do not go through validation.

**Raises**:

- `ModelDefinitionError`: if method has any other argument than self.

**Arguments**:

- `func` (`Callable`): decorated function to be exposed

**Returns**:

`Union[property, Callable]`: decorated function passed in func param, with set __property_field__ = True

