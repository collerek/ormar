import datetime

import databases
import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine

import ormar
from tests.settings import DATABASE_URL

metadata = sa.MetaData()
db = databases.Database(DATABASE_URL)
engine = create_engine(DATABASE_URL)


class User(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename = "users",
        metadata = metadata,
        database = db,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50, unique=True, index=True)


class RelationalAuditModel(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        abstract = True
    )

    created_by: User = ormar.ForeignKey(User, nullable=False)
    updated_by: User = ormar.ForeignKey(User, nullable=False)


class AuditModel(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        abstract = True
    )

    created_by: str = ormar.String(max_length=100)
    updated_by: str = ormar.String(max_length=100, default="Sam")


class DateFieldsModel(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        abstract = True,
        metadata = metadata,
        database = db,
    )

    created_date: datetime.datetime = ormar.DateTime(
        default=datetime.datetime.now, name="creation_date"
    )
    updated_date: datetime.datetime = ormar.DateTime(
        default=datetime.datetime.now, name="modification_date"
    )


class Category(DateFieldsModel, AuditModel):
    ormar_config = ormar.OrmarConfig(
        tablename = "categories",
        exclude_parent_fields = ["updated_by", "updated_date"],
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50, unique=True, index=True)
    code: int = ormar.Integer()


class Item(DateFieldsModel, AuditModel):
    ormar_config = ormar.OrmarConfig(
        tablename = "items",
        exclude_parent_fields = ["updated_by", "updated_date"],
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50, unique=True, index=True)
    code: int = ormar.Integer()
    updated_by: str = ormar.String(max_length=100, default="Bob")


class Gun(RelationalAuditModel, DateFieldsModel):
    ormar_config = ormar.OrmarConfig(
        tablename = "guns",
        exclude_parent_fields = ["updated_by"],
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


def test_model_definition():
    model_fields = Category.ormar_config.model_fields
    sqlalchemy_columns = Category.ormar_config.table.c
    pydantic_columns = Category.__fields__
    assert "updated_by" not in model_fields
    assert "updated_by" not in sqlalchemy_columns
    assert "updated_by" not in pydantic_columns
    assert "updated_date" not in model_fields
    assert "updated_date" not in sqlalchemy_columns
    assert "updated_date" not in pydantic_columns

    assert "updated_by" not in Gun.ormar_config.model_fields
    assert "updated_by" not in Gun.ormar_config.table.c
    assert "updated_by" not in Gun.__fields__


@pytest.mark.asyncio
async def test_model_works_as_expected():
    async with db:
        async with db.transaction(force_rollback=True):
            test = await Category(name="Cat", code=2, created_by="Joe").save()
            assert test.created_date is not None

            test2 = await Category.objects.get(pk=test.pk)
            assert test2.name == "Cat"
            assert test2.created_by == "Joe"


@pytest.mark.asyncio
async def test_exclude_with_redefinition():
    async with db:
        async with db.transaction(force_rollback=True):
            test = await Item(name="Item", code=3, created_by="Anna").save()
            assert test.created_date is not None
            assert test.updated_by == "Bob"

            test2 = await Item.objects.get(pk=test.pk)
            assert test2.name == "Item"
            assert test2.code == 3


@pytest.mark.asyncio
async def test_exclude_with_relation():
    async with db:
        async with db.transaction(force_rollback=True):
            user = await User(name="Michail Kalasznikow").save()
            test = await Gun(name="AK47", created_by=user).save()
            assert test.created_date is not None

            with pytest.raises(AttributeError):
                assert test.updated_by

            test2 = await Gun.objects.select_related("created_by").get(pk=test.pk)
            assert test2.name == "AK47"
            assert test2.created_by.name == "Michail Kalasznikow"
