import ormar
import pytest
import sqlalchemy

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Author(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="authors", schema='s1')

    id = ormar.Integer(primary_key=True)

class Book(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="books", schema='s1')

    id = ormar.Integer(primary_key=True)
    authors = ormar.ManyToMany(Author)

create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_m2m_auto_schema():
    async with base_ormar_config.database:
        insp = sqlalchemy.inspect(base_ormar_config.engine)
        assert insp.has_table("books_authors", schema="s1")
