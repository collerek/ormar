<a name="models.traversible"></a>
# models.traversible

<a name="models.traversible.NodeList"></a>
## NodeList Objects

```python
class NodeList()
```

Helper class that helps with iterating nested models

<a name="models.traversible.NodeList.add"></a>
#### add

```python
 | add(node_class: Type["RelationMixin"], relation_name: str = None, parent_node: "Node" = None) -> "Node"
```

Adds new Node or returns the existing one

**Arguments**:

- `node_class (ormar.models.metaclass.ModelMetaclass)`: Model in current node
- `relation_name (str)`: name of the current relation
- `parent_node (Optional[Node])`: parent node

**Returns**:

`(Node)`: returns new or already existing node

<a name="models.traversible.NodeList.find"></a>
#### find

```python
 | find(node_class: Type["RelationMixin"], relation_name: Optional[str] = None, parent_node: "Node" = None) -> Optional["Node"]
```

Searches for existing node with given parameters

**Arguments**:

- `node_class (ormar.models.metaclass.ModelMetaclass)`: Model in current node
- `relation_name (str)`: name of the current relation
- `parent_node (Optional[Node])`: parent node

**Returns**:

`(Optional[Node])`: returns already existing node or None

<a name="models.traversible.Node"></a>
## Node Objects

```python
class Node()
```

<a name="models.traversible.Node.visited"></a>
#### visited

```python
 | visited(relation_name: str) -> bool
```

Checks if given relation was already visited.

Relation was visited if it's name is in current node children.

Relation was visited if one of the parent node had the same Model class

**Arguments**:

- `relation_name (str)`: name of relation

**Returns**:

`(bool)`: result of the check

