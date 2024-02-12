import ormar.fields.constraints
import pytest

from tests.settings import create_config
from tests.lifespan import init_tests


base_ormar_config = create_config()


class Product(ormar.Model):
    ormar_config = base_ormar_config.copy(
        tablename="products",
        constraints=[
            ormar.fields.constraints.IndexColumns("company", "name", name="my_index"),
            ormar.fields.constraints.IndexColumns("location", "company_type"),
        ],
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    company: str = ormar.String(max_length=200)
    location: str = ormar.String(max_length=200)
    company_type: str = ormar.String(max_length=200)


create_test_database = init_tests(base_ormar_config)


def test_table_structure():
    assert len(Product.ormar_config.table.indexes) > 0
    indexes = sorted(
        list(Product.ormar_config.table.indexes), key=lambda x: x.name, reverse=True
    )
    test_index = indexes[0]
    assert test_index.name == "my_index"
    assert [col.name for col in test_index.columns] == ["company", "name"]

    test_index = indexes[1]
    assert test_index.name == "ix_products_location_company_type"
    assert [col.name for col in test_index.columns] == ["location", "company_type"]


@pytest.mark.asyncio
async def test_index_is_not_unique():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            await Product.objects.create(
                name="Cookies", company="Nestle", location="A", company_type="B"
            )
            await Product.objects.create(
                name="Mars", company="Mars", location="B", company_type="Z"
            )
            await Product.objects.create(
                name="Mars", company="Nestle", location="C", company_type="X"
            )
            await Product.objects.create(
                name="Mars", company="Mars", location="D", company_type="Y"
            )
