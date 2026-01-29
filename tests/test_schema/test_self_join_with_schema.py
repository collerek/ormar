import ormar
import pytest
from typing import ForwardRef

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


CategoryRef = ForwardRef('Category')

class Category(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="categories", schema='s1')

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)

    parent: "Category | None" = ormar.ForeignKey(
        CategoryRef,
        related_name="children",
        nullable=True,
    )

Category.update_forward_refs()

create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_self_join_select_related_and_reverse():
    async with base_ormar_config.database:
        root = await Category.objects.create(name="root")
        child = await Category.objects.create(name="child", parent=root)

        # self-join via select_related
        fetched_child = await Category.objects.select_related("parent").get(id=child.id)

        assert fetched_child.parent is not None
        assert fetched_child.parent.name == "root"

        # reverse relation (children)
        fetched_root = await Category.objects.prefetch_related("children").get(id=root.id)

        assert len(fetched_root.children) == 1
        assert fetched_root.children[0].name == "child"

