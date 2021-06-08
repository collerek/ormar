<a name="models.descriptors.descriptors"></a>
# models.descriptors.descriptors

<a name="models.descriptors.descriptors.PydanticDescriptor"></a>
## PydanticDescriptor Objects

```python
class PydanticDescriptor()
```

Pydantic descriptor simply delegates everything to pydantic model

<a name="models.descriptors.descriptors.JsonDescriptor"></a>
## JsonDescriptor Objects

```python
class JsonDescriptor()
```

Json descriptor dumps/loads strings to actual data on write/read

<a name="models.descriptors.descriptors.BytesDescriptor"></a>
## BytesDescriptor Objects

```python
class BytesDescriptor()
```

Bytes descriptor converts strings to bytes on write and converts bytes to str
if represent_as_base64_str flag is set, so the value can be dumped to json

<a name="models.descriptors.descriptors.PkDescriptor"></a>
## PkDescriptor Objects

```python
class PkDescriptor()
```

As of now it's basically a copy of PydanticDescriptor but that will
change in the future with multi column primary keys

<a name="models.descriptors.descriptors.RelationDescriptor"></a>
## RelationDescriptor Objects

```python
class RelationDescriptor()
```

Relation descriptor expands the relation to initialize the related model
before setting it to __dict__. Note that expanding also registers the
related model in RelationManager.

<a name="models.descriptors.descriptors.PropertyDescriptor"></a>
## PropertyDescriptor Objects

```python
class PropertyDescriptor()
```

Property descriptor handles methods decorated with @property_field decorator.
They are read only.

