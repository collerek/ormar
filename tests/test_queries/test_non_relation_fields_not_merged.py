from typing import Dict, List, Optional

import databases
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


base_ormar_config = ormar.OrmarConfig(
    metadata=metadata,
    database=database,
)

class Chart(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename = "authors")

    id: int = ormar.Integer(primary_key=True)
    datasets = ormar.JSON()


class Config(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename = "books")

    id: int = ormar.Integer(primary_key=True)
    chart: Optional[Chart] = ormar.ForeignKey(Chart)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_list_field_that_is_not_relation_is_not_merged():
    async with database:
        chart = await Chart.objects.create(datasets=[{"test": "ok"}])
        await Config.objects.create(chart=chart)
        await Config.objects.create(chart=chart)

        chart2 = await Chart.objects.select_related("configs").get()
        assert len(chart2.datasets) == 1
        assert chart2.datasets == [{"test": "ok"}]
