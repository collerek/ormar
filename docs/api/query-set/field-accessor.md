<a name="queryset.field_accessor"></a>
# queryset.field\_accessor

<a name="queryset.field_accessor.FieldAccessor"></a>
## FieldAccessor Objects

```python
class FieldAccessor()
```

Helper to access ormar fields directly from Model class also for nested
models attributes.

<a name="queryset.field_accessor.FieldAccessor.__bool__"></a>
#### \_\_bool\_\_

```python
 | __bool__() -> bool
```

Hack to avoid pydantic name check from parent model, returns false

**Returns**:

`(bool)`: False

<a name="queryset.field_accessor.FieldAccessor.__getattr__"></a>
#### \_\_getattr\_\_

```python
 | __getattr__(item: str) -> Any
```

Accessor return new accessor for each field and nested models.
Thanks to that operator overload is possible to use in filter.

**Arguments**:

- `item (str)`: attribute name

**Returns**:

`(ormar.queryset.field_accessor.FieldAccessor)`: FieldAccessor for field or nested model

<a name="queryset.field_accessor.FieldAccessor.__eq__"></a>
#### \_\_eq\_\_

```python
 | __eq__(other: Any) -> FilterGroup
```

overloaded to work as sql `column = <VALUE>`

**Arguments**:

- `other (str)`: value to check agains operator

**Returns**:

`(ormar.queryset.clause.FilterGroup)`: FilterGroup for operator

<a name="queryset.field_accessor.FieldAccessor.__ge__"></a>
#### \_\_ge\_\_

```python
 | __ge__(other: Any) -> FilterGroup
```

overloaded to work as sql `column >= <VALUE>`

**Arguments**:

- `other (str)`: value to check agains operator

**Returns**:

`(ormar.queryset.clause.FilterGroup)`: FilterGroup for operator

<a name="queryset.field_accessor.FieldAccessor.__gt__"></a>
#### \_\_gt\_\_

```python
 | __gt__(other: Any) -> FilterGroup
```

overloaded to work as sql `column > <VALUE>`

**Arguments**:

- `other (str)`: value to check agains operator

**Returns**:

`(ormar.queryset.clause.FilterGroup)`: FilterGroup for operator

<a name="queryset.field_accessor.FieldAccessor.__le__"></a>
#### \_\_le\_\_

```python
 | __le__(other: Any) -> FilterGroup
```

overloaded to work as sql `column <= <VALUE>`

**Arguments**:

- `other (str)`: value to check agains operator

**Returns**:

`(ormar.queryset.clause.FilterGroup)`: FilterGroup for operator

<a name="queryset.field_accessor.FieldAccessor.__lt__"></a>
#### \_\_lt\_\_

```python
 | __lt__(other: Any) -> FilterGroup
```

overloaded to work as sql `column < <VALUE>`

**Arguments**:

- `other (str)`: value to check agains operator

**Returns**:

`(ormar.queryset.clause.FilterGroup)`: FilterGroup for operator

<a name="queryset.field_accessor.FieldAccessor.__mod__"></a>
#### \_\_mod\_\_

```python
 | __mod__(other: Any) -> FilterGroup
```

overloaded to work as sql `column LIKE '%<VALUE>%'`

**Arguments**:

- `other (str)`: value to check agains operator

**Returns**:

`(ormar.queryset.clause.FilterGroup)`: FilterGroup for operator

<a name="queryset.field_accessor.FieldAccessor.__lshift__"></a>
#### \_\_lshift\_\_

```python
 | __lshift__(other: Any) -> FilterGroup
```

overloaded to work as sql `column IN (<VALUE1>, <VALUE2>,...)`

**Arguments**:

- `other (str)`: value to check agains operator

**Returns**:

`(ormar.queryset.clause.FilterGroup)`: FilterGroup for operator

<a name="queryset.field_accessor.FieldAccessor.__rshift__"></a>
#### \_\_rshift\_\_

```python
 | __rshift__(other: Any) -> FilterGroup
```

overloaded to work as sql `column IS NULL`

**Arguments**:

- `other (str)`: value to check agains operator

**Returns**:

`(ormar.queryset.clause.FilterGroup)`: FilterGroup for operator

<a name="queryset.field_accessor.FieldAccessor.in_"></a>
#### in\_

```python
 | in_(other: Any) -> FilterGroup
```

works as sql `column IN (<VALUE1>, <VALUE2>,...)`

**Arguments**:

- `other (str)`: value to check agains operator

**Returns**:

`(ormar.queryset.clause.FilterGroup)`: FilterGroup for operator

<a name="queryset.field_accessor.FieldAccessor.iexact"></a>
#### iexact

```python
 | iexact(other: Any) -> FilterGroup
```

works as sql `column = <VALUE>` case-insensitive

**Arguments**:

- `other (str)`: value to check agains operator

**Returns**:

`(ormar.queryset.clause.FilterGroup)`: FilterGroup for operator

<a name="queryset.field_accessor.FieldAccessor.contains"></a>
#### contains

```python
 | contains(other: Any) -> FilterGroup
```

works as sql `column LIKE '%<VALUE>%'`

**Arguments**:

- `other (str)`: value to check agains operator

**Returns**:

`(ormar.queryset.clause.FilterGroup)`: FilterGroup for operator

<a name="queryset.field_accessor.FieldAccessor.icontains"></a>
#### icontains

```python
 | icontains(other: Any) -> FilterGroup
```

works as sql `column LIKE '%<VALUE>%'` case-insensitive

**Arguments**:

- `other (str)`: value to check agains operator

**Returns**:

`(ormar.queryset.clause.FilterGroup)`: FilterGroup for operator

<a name="queryset.field_accessor.FieldAccessor.startswith"></a>
#### startswith

```python
 | startswith(other: Any) -> FilterGroup
```

works as sql `column LIKE '<VALUE>%'`

**Arguments**:

- `other (str)`: value to check agains operator

**Returns**:

`(ormar.queryset.clause.FilterGroup)`: FilterGroup for operator

<a name="queryset.field_accessor.FieldAccessor.istartswith"></a>
#### istartswith

```python
 | istartswith(other: Any) -> FilterGroup
```

works as sql `column LIKE '%<VALUE>'` case-insensitive

**Arguments**:

- `other (str)`: value to check agains operator

**Returns**:

`(ormar.queryset.clause.FilterGroup)`: FilterGroup for operator

<a name="queryset.field_accessor.FieldAccessor.endswith"></a>
#### endswith

```python
 | endswith(other: Any) -> FilterGroup
```

works as sql `column LIKE '%<VALUE>'`

**Arguments**:

- `other (str)`: value to check agains operator

**Returns**:

`(ormar.queryset.clause.FilterGroup)`: FilterGroup for operator

<a name="queryset.field_accessor.FieldAccessor.iendswith"></a>
#### iendswith

```python
 | iendswith(other: Any) -> FilterGroup
```

works as sql `column LIKE '%<VALUE>'` case-insensitive

**Arguments**:

- `other (str)`: value to check agains operator

**Returns**:

`(ormar.queryset.clause.FilterGroup)`: FilterGroup for operator

<a name="queryset.field_accessor.FieldAccessor.isnull"></a>
#### isnull

```python
 | isnull(other: Any) -> FilterGroup
```

works as sql `column IS NULL` or `IS NOT NULL`

**Arguments**:

- `other (str)`: value to check agains operator

**Returns**:

`(ormar.queryset.clause.FilterGroup)`: FilterGroup for operator

<a name="queryset.field_accessor.FieldAccessor.asc"></a>
#### asc

```python
 | asc() -> OrderAction
```

works as sql `column asc`

**Returns**:

`(ormar.queryset.actions.OrderGroup)`: OrderGroup for operator

<a name="queryset.field_accessor.FieldAccessor.desc"></a>
#### desc

```python
 | desc() -> OrderAction
```

works as sql `column desc`

**Returns**:

`(ormar.queryset.actions.OrderGroup)`: OrderGroup for operator

