import ormar
import pytest
import sqlalchemy

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class User(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="users", schema='s1')

    id = ormar.Integer(primary_key=True)

class Profile(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="profiles", schema='s1')

    id = ormar.Integer(primary_key=True)
    user = ormar.ForeignKey(User)

create_test_database = init_tests(base_ormar_config)

@pytest.mark.asyncio
async def test_fk_resolves_schema():
    async with base_ormar_config.database:
        insp = sqlalchemy.inspect(base_ormar_config.engine)
        fks = insp.get_foreign_keys("profiles", schema="s1")

        assert len(fks) == 1
        assert fks[0]["referred_table"] == "users"
        assert fks[0]["referred_schema"] == "s1"