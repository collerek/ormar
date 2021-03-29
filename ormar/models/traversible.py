from typing import Any, List, Optional, TYPE_CHECKING, Type

if TYPE_CHECKING:  # pragma no cover
    from ormar.models.mixins.relation_mixin import RelationMixin


class NodeList:
    """
    Helper class that helps with iterating nested models
    """

    def __init__(self) -> None:
        self.node_list: List["Node"] = []

    def __getitem__(self, item: Any) -> Any:
        return self.node_list.__getitem__(item)

    def add(
        self,
        node_class: Type["RelationMixin"],
        relation_name: str = None,
        parent_node: "Node" = None,
    ) -> "Node":
        """
        Adds new Node or returns the existing one

        :param node_class: Model in current node
        :type node_class: ormar.models.metaclass.ModelMetaclass
        :param relation_name: name of the current relation
        :type relation_name: str
        :param parent_node: parent node
        :type parent_node: Optional[Node]
        :return: returns new or already existing node
        :rtype: Node
        """
        existing_node = self.find(
            relation_name=relation_name, node_class=node_class, parent_node=parent_node
        )
        if not existing_node:
            current_node = Node(
                node_class=node_class,
                relation_name=relation_name,
                parent_node=parent_node,
            )
            self.node_list.append(current_node)
            return current_node
        return existing_node  # pragma: no cover

    def find(
        self,
        node_class: Type["RelationMixin"],
        relation_name: Optional[str] = None,
        parent_node: "Node" = None,
    ) -> Optional["Node"]:
        """
        Searches for existing node with given parameters

        :param node_class: Model in current node
        :type node_class: ormar.models.metaclass.ModelMetaclass
        :param relation_name: name of the current relation
        :type relation_name: str
        :param parent_node: parent node
        :type parent_node: Optional[Node]
        :return: returns already existing node or None
        :rtype: Optional[Node]
        """
        for node in self.node_list:
            if (
                node.node_class == node_class
                and node.parent_node == parent_node
                and node.relation_name == relation_name
            ):
                return node  # pragma: no cover
        return None


class Node:
    def __init__(
        self,
        node_class: Type["RelationMixin"],
        relation_name: str = None,
        parent_node: "Node" = None,
    ) -> None:
        self.relation_name = relation_name
        self.node_class = node_class
        self.parent_node = parent_node
        self.visited_children: List["Node"] = []
        if self.parent_node:
            self.parent_node.visited_children.append(self)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"{self.node_class.get_name(lower=False)}, "
            f"relation:{self.relation_name}, "
            f"parent: {self.parent_node}"
        )

    def visited(self, relation_name: str) -> bool:
        """
        Checks if given relation was already visited.

        Relation was visited if it's name is in current node children.

        Relation was visited if one of the parent node had the same Model class

        :param relation_name: name of relation
        :type relation_name: str
        :return: result of the check
        :rtype: bool
        """
        target_model = self.node_class.Meta.model_fields[relation_name].to
        if self.parent_node:
            node = self
            while node.parent_node:
                node = node.parent_node
                if node.node_class == target_model:
                    return True
        return False
