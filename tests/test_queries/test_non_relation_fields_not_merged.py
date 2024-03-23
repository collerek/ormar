from typing import Optional

import ormar
import pytest

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Chart(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="authors")

    id: int = ormar.Integer(primary_key=True)
    datasets = ormar.JSON()


class Config(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="books")

    id: int = ormar.Integer(primary_key=True)
    chart: Optional[Chart] = ormar.ForeignKey(Chart)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_list_field_that_is_not_relation_is_not_merged():
    async with base_ormar_config.database:
        chart = await Chart.objects.create(datasets=[{"test": "ok"}])
        await Config.objects.create(chart=chart)
        await Config.objects.create(chart=chart)

        chart2 = await Chart.objects.select_related("configs").get()
        assert len(chart2.datasets) == 1
        assert chart2.datasets == [{"test": "ok"}]
