import pytest
import sqlalchemy

import ormar.fields.constraints
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Product(ormar.Model):
    ormar_config = base_ormar_config.copy(
        tablename="products",
        constraints=[
            ormar.fields.constraints.CheckColumns("inventory > buffer"),
        ],
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    company: str = ormar.String(max_length=200)
    inventory: int = ormar.Integer()
    buffer: int = ormar.Integer()


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_check_columns_exclude_mysql():
    async with base_ormar_config.database:  # pragma: no cover
        if Product.ormar_config.database.dialect.name != "mysql":
            async with base_ormar_config.database.transaction(force_rollback=True):
                await Product.objects.create(
                    name="Mars", company="Nestle", inventory=100, buffer=10
                )

                with pytest.raises((sqlalchemy.exc.IntegrityError)):
                    await Product.objects.create(
                        name="Cookies", company="Nestle", inventory=1, buffer=10
                    )
