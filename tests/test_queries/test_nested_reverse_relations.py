from typing import Optional

import pytest

import ormar
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class DataSource(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="datasources")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=200, unique=True, index=True)


class DataSourceTable(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="source_tables")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=200, index=True)
    source: Optional[DataSource] = ormar.ForeignKey(
        DataSource, name="source_id", related_name="tables", ondelete="CASCADE"
    )


class DataSourceTableColumn(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="source_columns")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=200, index=True)
    data_type: str = ormar.String(max_length=200)
    table: Optional[DataSourceTable] = ormar.ForeignKey(
        DataSourceTable, name="table_id", related_name="columns", ondelete="CASCADE"
    )


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_double_nested_reverse_relation():
    async with base_ormar_config.database:
        data_source = await DataSource(name="local").save()
        test_tables = [
            {
                "name": "test1",
                "columns": [
                    {"name": "col1", "data_type": "test"},
                    {"name": "col2", "data_type": "test2"},
                    {"name": "col3", "data_type": "test3"},
                ],
            },
            {
                "name": "test2",
                "columns": [
                    {"name": "col4", "data_type": "test"},
                    {"name": "col5", "data_type": "test2"},
                    {"name": "col6", "data_type": "test3"},
                ],
            },
        ]
        data_source.tables = test_tables
        await data_source.save_related(save_all=True, follow=True)

        tables = await DataSourceTable.objects.all()
        assert len(tables) == 2

        columns = await DataSourceTableColumn.objects.all()
        assert len(columns) == 6

        data_source = (
            await DataSource.objects.select_related("tables__columns")
            .filter(tables__name__in=["test1", "test2"], name="local")
            .get()
        )
        assert len(data_source.tables) == 2
        assert len(data_source.tables[0].columns) == 3
        assert data_source.tables[0].columns[0].name == "col1"
        assert data_source.tables[0].columns[2].name == "col3"
        assert len(data_source.tables[1].columns) == 3
        assert data_source.tables[1].columns[0].name == "col4"
        assert data_source.tables[1].columns[2].name == "col6"
