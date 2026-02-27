import pytest

import ormar
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Jimmy(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="jimmies")
    name = ormar.String(primary_key=True, max_length=42)


create_test_database = init_tests(base_ormar_config)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="function", autouse=True)
async def db_session():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            yield


@pytest.mark.anyio
async def test_jimmy_can():
    await Jimmy.objects.create(
        name="jimmy",
    )
    await Jimmy.objects.create(
        name="jimmyRus",
    )
    jimmies = await Jimmy.objects.all()
    assert len(jimmies) == 2


@pytest.mark.anyio
async def test_jimmy_cant():
    jimmies = await Jimmy.objects.all()
    assert not jimmies

    await Jimmy.objects.create(
        name="jimmy",
    )
    await Jimmy.objects.create(
        name="jimmyRus",
    )
    jimmies = await Jimmy.objects.all()
    assert len(jimmies) == 2
