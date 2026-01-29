import datetime
from typing import Optional

import ormar
import pytest

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class TableBase(ormar.Model):
    ormar_config = base_ormar_config.copy(abstract=True)

    id: int = ormar.Integer(primary_key=True)
    created_by: str = ormar.String(max_length=20, default="test")
    created_at: datetime.datetime = ormar.DateTime(
        timezone=True, default=datetime.datetime.now
    )
    last_modified_by: Optional[str] = ormar.String(max_length=20, nullable=True)
    last_modified_at: Optional[datetime.datetime] = ormar.DateTime(
        timezone=True, nullable=True
    )


class NationBase(ormar.Model):
    ormar_config = base_ormar_config.copy(abstract=True)

    name: str = ormar.String(max_length=50)
    alpha2_code: str = ormar.String(max_length=2)
    region: str = ormar.String(max_length=30)
    subregion: str = ormar.String(max_length=30)


class Nation(NationBase, TableBase):
    ormar_config = base_ormar_config.copy()


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_model_is_not_abstract_by_default():
    async with base_ormar_config.database:
        sweden = await Nation(
            name="Sweden", alpha2_code="SE", region="Europe", subregion="Scandinavia"
        ).save()
        assert sweden.id is not None
