import databases
import pytest
from sqlalchemy import func

import ormar
import sqlalchemy
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Chart(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename = "charts",
        database = database,
        metadata = metadata,
    )

    chart_id = ormar.Integer(primary_key=True, autoincrement=True)
    name = ormar.String(max_length=200, unique=True, index=True)
    query_text = ormar.Text()
    datasets = ormar.JSON()
    layout = ormar.JSON()
    data_config = ormar.JSON()
    created_date = ormar.DateTime(server_default=func.now())
    library = ormar.String(max_length=200, default="plotly")
    used_filters = ormar.JSON()


class Report(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename = "reports",
        database = database,
        metadata = metadata,
    )

    report_id = ormar.Integer(primary_key=True, autoincrement=True)
    name = ormar.String(max_length=200, unique=True, index=True)
    filters_position = ormar.String(max_length=200)
    created_date = ormar.DateTime(server_default=func.now())


class Language(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename = "languages",
        database = database,
        metadata = metadata,
    )

    language_id = ormar.Integer(primary_key=True, autoincrement=True)
    code = ormar.String(max_length=5)
    name = ormar.String(max_length=200)


class TranslationNode(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename = "translation_nodes",
        database = database,
        metadata = metadata,
    )

    node_id = ormar.Integer(primary_key=True, autoincrement=True)
    node_type = ormar.String(max_length=200)


class Translation(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename = "translations",
        database = database,
        metadata = metadata,
    )

    translation_id = ormar.Integer(primary_key=True, autoincrement=True)
    node_id = ormar.ForeignKey(TranslationNode, related_name="translations")
    language = ormar.ForeignKey(Language, name="language_id")
    value = ormar.String(max_length=500)


class Filter(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename = "filters",
        database = database,
        metadata = metadata,
    )

    filter_id = ormar.Integer(primary_key=True, autoincrement=True)
    name = ormar.String(max_length=200, unique=True, index=True)
    label = ormar.String(max_length=200)
    query_text = ormar.Text()
    allow_multiselect = ormar.Boolean(default=True)
    created_date = ormar.DateTime(server_default=func.now())
    is_dynamic = ormar.Boolean(default=True)
    is_date = ormar.Boolean(default=False)
    translation = ormar.ForeignKey(TranslationNode, name="translation_node_id")


class FilterValue(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename = "filter_values",
        database = database,
        metadata = metadata,
    )

    value_id = ormar.Integer(primary_key=True, autoincrement=True)
    value = ormar.String(max_length=300)
    label = ormar.String(max_length=300)
    filter = ormar.ForeignKey(Filter, name="filter_id", related_name="values")
    translation = ormar.ForeignKey(TranslationNode, name="translation_node_id")


class FilterXReport(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename = "filters_x_reports",
        database = database,
        metadata = metadata,
    )

    filter_x_report_id = ormar.Integer(primary_key=True)
    filter = ormar.ForeignKey(Filter, name="filter_id", related_name="reports")
    report = ormar.ForeignKey(Report, name="report_id", related_name="filters")
    sort_order = ormar.Integer()
    default_value = ormar.Text()
    is_visible = ormar.Boolean()


class ChartXReport(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename = "charts_x_reports",
        database = database,
        metadata = metadata,
    )

    chart_x_report_id = ormar.Integer(primary_key=True)
    chart = ormar.ForeignKey(Chart, name="chart_id", related_name="reports")
    report = ormar.ForeignKey(Report, name="report_id", related_name="charts")
    sort_order = ormar.Integer()
    width = ormar.Integer()


class ChartColumn(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename = "charts_columns",
        database = database,
        metadata = metadata,
    )

    column_id = ormar.Integer(primary_key=True, autoincrement=True)
    chart = ormar.ForeignKey(Chart, name="chart_id", related_name="columns")
    column_name = ormar.String(max_length=200)
    column_type = ormar.String(max_length=200)
    translation = ormar.ForeignKey(TranslationNode, name="translation_node_id")


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_saving_related_fk_rel():
    async with database:
        async with database.transaction(force_rollback=True):
            await Report.objects.select_all(follow=True).all()
