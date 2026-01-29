import ormar
import pytest
import sqlalchemy

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Category(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="categories", schema='test')

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50, unique=True, index=True)
    code: int = ormar.Integer()


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_table_in_schema():
    async with base_ormar_config.database:
        insp = sqlalchemy.inspect(base_ormar_config.engine)
        assert insp.has_table("categories", schema="test")