import time
import uuid
from contextlib import nullcontext
from datetime import datetime

import ormar
import pytest
from ormar import ModelDefinitionError
from sqlalchemy import func, text

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Product(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="product")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    company: str = ormar.String(max_length=200, server_default="Acme")
    sort_order: int = ormar.Integer(server_default=text("10"))
    created: datetime = ormar.DateTime(server_default=func.now())


def get_server_default_function() -> str:
    dialect = base_ormar_config.database._backend._dialect.name

    uuid_funct = {
        "postgresql": "gen_random_uuid()",
        "mysql": "UUID()",
        "sqlite": str(uuid.uuid4()),
    }
    return uuid_funct[dialect]


class ServerId(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="server_ids")

    id: uuid.UUID = ormar.UUID(
        primary_key=True,
        server_default=get_server_default_function(),
        uuid_format="string",
    )
    name: str = ormar.String(max_length=100)


create_test_database = init_tests(base_ormar_config)


def test_table_defined_properly():
    assert Product.ormar_config.model_fields["created"].nullable
    assert not Product.model_fields["created"].is_required()
    assert (
        Product.ormar_config.table.columns["created"].server_default.arg.name == "now"
    )


@pytest.mark.asyncio
async def test_model_creation():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            p1 = Product(name="Test")
            assert p1.created is None
            await p1.save()
            await p1.load()
            assert p1.created is not None
            assert p1.company == "Acme"
            assert p1.sort_order == 10

            date = datetime.strptime("2020-10-27 11:30", "%Y-%m-%d %H:%M")
            p3 = await Product.objects.create(
                name="Test2", created=date, company="Roadrunner", sort_order=1
            )
            assert p3.created is not None
            assert p3.created == date
            assert p1.created != p3.created
            assert p3.company == "Roadrunner"
            assert p3.sort_order == 1

            p3 = await Product.objects.get(name="Test2")
            assert p3.company == "Roadrunner"
            assert p3.sort_order == 1

            time.sleep(1)

            p2 = await Product.objects.create(name="Test3")
            assert p2.created is not None
            assert p2.company == "Acme"
            assert p2.sort_order == 10

            if Product.db_backend_name() != "postgresql":
                # postgres use transaction timestamp so it will remain the same
                assert p1.created != p2.created  # pragma nocover


@pytest.mark.asyncio
async def test_uuid_server_function():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            with (
                pytest.raises(ModelDefinitionError)
                if base_ormar_config.database._backend._dialect.name == "sqlite"
                else nullcontext()
            ):
                await ServerId(name="test").save()
