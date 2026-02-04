import ormar
import pytest
from ormar.databases.connection import DatabaseConnection
from sqlalchemy import text

from tests.lifespan import init_tests
from tests.settings import ASYNC_DATABASE_URL, DATABASE_URL, create_config

base_ormar_config = create_config()


class Team(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="teams")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


create_test_database = init_tests(base_ormar_config)


def test_url_is_replaced_to_async_and_accessible():
    database = DatabaseConnection(ASYNC_DATABASE_URL)
    assert database.url == ASYNC_DATABASE_URL

    expected_drivers = {
        "mysql": "mysql+aiomysql",
        "sqlite": "sqlite+aiosqlite",
        "postgresql": "postgresql+asyncpg",
    }

    dialect = DATABASE_URL.split(":")[0]
    assert dialect in expected_drivers
    assert expected_drivers[dialect] in database.url


@pytest.mark.asyncio
async def test_getting_raw_connection():
    database = DatabaseConnection(ASYNC_DATABASE_URL)
    async with database:
        async with database.connection() as conn:
            result = await conn.execute(text("SELECT 123"))
            async with database.transaction():
                async with database.connection() as conn2:
                    assert conn2 != conn
                async with database.connection() as conn3:
                    assert conn3 == conn2
                    async with database.connection() as conn4:
                        assert conn4 != conn
                        assert conn3 == conn4
            async with database.connection() as conn5:
                assert conn5 != conn4
                assert conn5 != conn
    assert result.fetchone()[0] == 123


@pytest.mark.asyncio
async def test_getting_commit_in_transaction():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction() as tran:
            assert tran._depth == 0
            await Team.objects.create(name="Red Team")
            await Team.objects.create(name="Blue Team")
            async with base_ormar_config.database.transaction() as tran2:
                assert tran2._depth == 1
                await Team.objects.create(name="Yellow Team")
            yellow = await Team.objects.get(name="Yellow Team")
            yellow.name = "Green Team"
            await yellow.update()

        teams = await Team.objects.all()
        assert len(teams) == 3
        assert {teams.name for teams in teams} == {
            "Red Team",
            "Blue Team",
            "Green Team",
        }
