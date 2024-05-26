import ormar
import pytest

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class A(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id = ormar.Integer(primary_key=True)


class B(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id = ormar.Integer(primary_key=True)
    a = ormar.ForeignKey(A)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_saving_related_pk_only():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            a = A()
            await a.save()
            await a.save_related(follow=True, save_all=True)
