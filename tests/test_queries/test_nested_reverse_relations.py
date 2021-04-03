from typing import Optional

import databases
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class DataSource(ormar.Model):
    class Meta(BaseMeta):
        tablename = "datasources"

    source_id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=200, unique=True, index=True)


class DataSourceTable(ormar.Model):
    class Meta(BaseMeta):
        tablename = "datasource_tables"

    datasource_table_id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=200, index=True)
    data_source: Optional[DataSource] = ormar.ForeignKey(
        DataSource,
        name="data_source_id",
        related_name="datasource_tables",
        ondelete="CASCADE",
    )


class DataSourceTableColumn(ormar.Model):
    class Meta(BaseMeta):
        tablename = "datasource_table_columns"

    datasource_table_column_id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=200, index=True)
    data_type: str = ormar.String(max_length=200)
    datasource_table: Optional[DataSourceTable] = ormar.ForeignKey(
        DataSourceTable,
        name="datasource_table_id",
        related_name="datasource_table_columns",
        ondelete="CASCADE",
    )


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_double_nested_reverse_relation():
    async with database:
        data_source = await DataSource(name="local").save()
        test_tables = [
            {
                "name": "test1",
                "datasource_table_columns": [
                    {"name": "col1", "data_type": "test"},
                    {"name": "col2", "data_type": "test2"},
                    {"name": "col3", "data_type": "test3"},
                ],
            },
            {
                "name": "test2",
                "datasource_table_columns": [
                    {"name": "col4", "data_type": "test"},
                    {"name": "col5", "data_type": "test2"},
                    {"name": "col6", "data_type": "test3"},
                ],
            },
        ]
        data_source.datasource_tables = test_tables
        await data_source.save_related(save_all=True, follow=True)

        tables = await DataSourceTable.objects.all()
        assert len(tables) == 2

        columns = await DataSourceTableColumn.objects.all()
        assert len(columns) == 6

        data_source = (
            await DataSource.objects.select_related(
                "datasource_tables__datasource_table_columns"
            )
            .filter(datasource_tables__name__in=["test1", "test2"], name="local")
            .get()
        )
        assert len(data_source.datasource_tables) == 2
        assert len(data_source.datasource_tables[0].datasource_table_columns) == 3
        assert (
            data_source.datasource_tables[0].datasource_table_columns[0].name == "col1"
        )
        assert (
            data_source.datasource_tables[0].datasource_table_columns[2].name == "col3"
        )
        assert len(data_source.datasource_tables[1].datasource_table_columns) == 3
        assert (
            data_source.datasource_tables[1].datasource_table_columns[0].name == "col4"
        )
        assert (
            data_source.datasource_tables[1].datasource_table_columns[2].name == "col6"
        )
