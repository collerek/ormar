import datetime
from typing import List, Optional

import databases
import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine

import ormar
from ormar import ModelDefinitionError, property_field
from ormar.exceptions import ModelError
from tests.settings import DATABASE_URL

metadata = sa.MetaData()
db = databases.Database(DATABASE_URL)
engine = create_engine(DATABASE_URL)


class AuditModel(ormar.Model):
    class Meta:
        abstract = True

    created_by: str = ormar.String(max_length=100)
    updated_by: str = ormar.String(max_length=100, default="Sam")


class DateFieldsModel(ormar.Model):
    class Meta(ormar.ModelMeta):
        abstract = True
        metadata = metadata
        database = db

    created_date: datetime.datetime = ormar.DateTime(
        default=datetime.datetime.now, name="creation_date"
    )
    updated_date: datetime.datetime = ormar.DateTime(
        default=datetime.datetime.now, name="modification_date"
    )


class Category(DateFieldsModel, AuditModel):
    class Meta(ormar.ModelMeta):
        tablename = "categories"
        exclude_parent_fields = ["updated_by", "updated_date"]

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50, unique=True, index=True)
    code: int = ormar.Integer()


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


def test_model_definition():
    model_fields = Category.Meta.model_fields
    sqlalchemy_columns = Category.Meta.table.c
    pydantic_columns = Category.__fields__
    assert "updated_by" not in model_fields
    assert "updated_by" not in sqlalchemy_columns
    assert "updated_by" not in pydantic_columns
    assert "updated_date" not in model_fields
    assert "updated_date" not in sqlalchemy_columns
    assert "updated_date" not in pydantic_columns
