from datetime import datetime

import pytest

import ormar
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Node(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="node")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=120)
    type: str = ormar.String(max_length=12, default="FLOW")
    created_at: datetime = ormar.DateTime(timezone=True, default=datetime.now)


class Edge(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="edge")

    id: str = ormar.String(primary_key=True, max_length=12)
    src_node: Node = ormar.ForeignKey(Node, related_name="next_edges")
    dst_node: Node = ormar.ForeignKey(Node, related_name="previous_edges")
    order: int = ormar.Integer(default=1)
    created_at: datetime = ormar.DateTime(timezone=True, default=datetime.now)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_sort_order_on_main_model():
    async with base_ormar_config.database:
        node1 = await Node(name="Node 1").save()
        node2 = await Node(name="Node 2").save()
        node3 = await Node(name="Node 3").save()

        await Edge(id="Side 1", src_node=node1, dst_node=node2).save()
        await Edge(id="Side 2", src_node=node2, dst_node=node3, order=2).save()
        await Edge(id="Side 3", src_node=node3, dst_node=node1, order=3).save()

        active_nodes = await Node.objects.select_related(
            ["next_edges", "next_edges__dst_node"]
        ).all()

        assert len(active_nodes) == 3
        assert active_nodes[0].next_edges[0].id == "Side 1"
        assert active_nodes[0].next_edges[0].dst_node.type == "FLOW"
