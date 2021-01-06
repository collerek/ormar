<a name="exceptions"></a>
# exceptions

Gathers all exceptions thrown by ormar.

<a name="exceptions.AsyncOrmException"></a>
## AsyncOrmException Objects

```python
class AsyncOrmException(Exception)
```

Base ormar Exception

<a name="exceptions.ModelDefinitionError"></a>
## ModelDefinitionError Objects

```python
class ModelDefinitionError(AsyncOrmException)
```

Raised for errors related to the model definition itself:

* setting @property_field on method with arguments other than func(self)
* defining a Field without required parameters
* defining a model with more than one primary_key
* defining a model without primary_key
* setting primary_key column as pydantic_only

<a name="exceptions.ModelError"></a>
## ModelError Objects

```python
class ModelError(AsyncOrmException)
```

Raised for initialization of model with non-existing field keyword.

<a name="exceptions.NoMatch"></a>
## NoMatch Objects

```python
class NoMatch(AsyncOrmException)
```

Raised for database queries that has no matching result (empty result).

<a name="exceptions.MultipleMatches"></a>
## MultipleMatches Objects

```python
class MultipleMatches(AsyncOrmException)
```

Raised for database queries that should return one row (i.e. get, first etc.)
but has multiple matching results in response.

<a name="exceptions.QueryDefinitionError"></a>
## QueryDefinitionError Objects

```python
class QueryDefinitionError(AsyncOrmException)
```

Raised for errors in query definition:

* using contains or icontains filter with instance of the Model
* using Queryset.update() without filter and setting each flag to True
* using Queryset.delete() without filter and setting each flag to True

<a name="exceptions.ModelPersistenceError"></a>
## ModelPersistenceError Objects

```python
class ModelPersistenceError(AsyncOrmException)
```

Raised for update of models without primary_key set (cannot retrieve from db)
or for saving a model with relation to unsaved model (cannot extract fk value).

<a name="exceptions.SignalDefinitionError"></a>
## SignalDefinitionError Objects

```python
class SignalDefinitionError(AsyncOrmException)
```

Raised when non callable receiver is passed as signal callback.

