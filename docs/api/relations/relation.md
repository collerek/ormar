<a name="relations.relation"></a>
# relations.relation

<a name="relations.relation.RelationType"></a>
## RelationType Objects

```python
class RelationType(Enum)
```

Different types of relations supported by ormar:

*  ForeignKey = PRIMARY
*  reverse ForeignKey = REVERSE
*  ManyToMany = MULTIPLE

<a name="relations.relation.RelationType.PRIMARY"></a>
#### PRIMARY

<a name="relations.relation.RelationType.REVERSE"></a>
#### REVERSE

<a name="relations.relation.RelationType.MULTIPLE"></a>
#### MULTIPLE

<a name="relations.relation.Relation"></a>
## Relation Objects

```python
class Relation()
```

Keeps related Models and handles adding/removing of the children.

<a name="relations.relation.Relation.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(manager: "RelationsManager", type_: RelationType, field_name: str, to: Type["T"], through: Type["T"] = None) -> None
```

Initialize the Relation and keep the related models either as instances of
passed Model, or as a RelationProxy which is basically a list of models with
some special behavior, as it exposes QuerySetProxy and allows querying the
related models already pre filtered by parent model.

**Arguments**:

- `manager (RelationsManager)`: reference to relation manager
- `type_ (RelationType)`: type of the relation
- `field_name (str)`: name of the relation field
- `to (Type[Model])`: model to which relation leads to
- `through (Type[Model])`: model through which relation goes for m2m relations

<a name="relations.relation.Relation._clean_related"></a>
#### \_clean\_related

```python
 | _clean_related() -> None
```

Removes dead weakrefs from RelationProxy.

<a name="relations.relation.Relation._find_existing"></a>
#### \_find\_existing

```python
 | _find_existing(child: Union["NewBaseModel", Type["NewBaseModel"]]) -> Optional[int]
```

Find child model in RelationProxy if exists.

**Arguments**:

- `child (Model)`: child model to find

**Returns**:

`(Optional[ind])`: index of child in RelationProxy

<a name="relations.relation.Relation.add"></a>
#### add

```python
 | add(child: "T") -> None
```

Adds child Model to relation, either sets child as related model or adds
it to the list in RelationProxy depending on relation type.

**Arguments**:

- `child (Model)`: model to add to relation

<a name="relations.relation.Relation.remove"></a>
#### remove

```python
 | remove(child: Union["NewBaseModel", Type["NewBaseModel"]]) -> None
```

Removes child Model from relation, either sets None as related model or removes
it from the list in RelationProxy depending on relation type.

**Arguments**:

- `child (Model)`: model to remove from relation

<a name="relations.relation.Relation.get"></a>
#### get

```python
 | get() -> Optional[Union[List["T"], "T"]]
```

Return the related model or models from RelationProxy.

**Returns**:

`(Optional[Union[List[Model], Model]])`: related model/models if set

<a name="relations.relation.Relation.__repr__"></a>
#### \_\_repr\_\_

```python
 | __repr__() -> str
```

