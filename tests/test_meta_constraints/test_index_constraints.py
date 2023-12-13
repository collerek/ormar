import asyncpg  # type: ignore
import databases
import pytest
import sqlalchemy

import ormar.fields.constraints
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Product(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename = "products",
        metadata = metadata,
        database = database,
        constraints = [
            ormar.fields.constraints.IndexColumns("company", "name", name="my_index"),
            ormar.fields.constraints.IndexColumns("location", "company_type"),
        ]
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    company: str = ormar.String(max_length=200)
    location: str = ormar.String(max_length=200)
    company_type: str = ormar.String(max_length=200)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


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
    async with database:
        async with database.transaction(force_rollback=True):
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
