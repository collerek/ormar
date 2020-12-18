# type: ignore
import datetime
from typing import Optional

import databases
import pytest
import sqlalchemy
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

    @property_field
    def audit(self):  # pragma: no cover
        return f"{self.created_by} {self.updated_by}"


class DateFieldsModelNoSubclass(ormar.Model):
    class Meta:
        tablename = "test_date_models"
        metadata = metadata
        database = db

    date_id: int = ormar.Integer(primary_key=True)
    created_date: datetime.datetime = ormar.DateTime(default=datetime.datetime.now)
    updated_date: datetime.datetime = ormar.DateTime(default=datetime.datetime.now)


class DateFieldsModel(ormar.Model):
    class Meta:
        abstract = True
        metadata = metadata
        database = db
        constraints = [ormar.UniqueColumns("creation_date", "modification_date")]

    created_date: datetime.datetime = ormar.DateTime(
        default=datetime.datetime.now, name="creation_date"
    )
    updated_date: datetime.datetime = ormar.DateTime(
        default=datetime.datetime.now, name="modification_date"
    )


class Category(DateFieldsModel, AuditModel):
    class Meta(ormar.ModelMeta):
        tablename = "categories"
        constraints = [ormar.UniqueColumns("name", "code")]

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50, unique=True, index=True)
    code: int = ormar.Integer()

    @property_field
    def code_name(self):
        return f"{self.code}:{self.name}"

    @property_field
    def audit(self):
        return f"{self.created_by} {self.updated_by}"


class Subject(DateFieldsModel):
    class Meta(ormar.ModelMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50, unique=True, index=True)
    category: Optional[Category] = ormar.ForeignKey(Category)


class Person(ormar.Model):
    class Meta:
        metadata = metadata
        database = db

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Car(ormar.Model):
    class Meta:
        abstract = True
        metadata = metadata
        database = db

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50)
    owner: Person = ormar.ForeignKey(Person)
    co_owner: Person = ormar.ForeignKey(Person, related_name="coowned")


class Truck(Car):
    class Meta:
        metadata = metadata
        database = db

    max_capacity: int = ormar.Integer()


class Bus(Car):
    class Meta:
        tablename = "buses"
        metadata = metadata
        database = db

    max_persons: int = ormar.Integer()


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


def test_init_of_abstract_model():
    with pytest.raises(ModelError):
        DateFieldsModel()


def test_field_redefining_in_concrete_models():
    class RedefinedField(DateFieldsModel):
        class Meta(ormar.ModelMeta):
            tablename = "redefines"
            metadata = metadata
            database = db

        id: int = ormar.Integer(primary_key=True)
        created_date: str = ormar.String(max_length=200, name="creation_date")

    changed_field = RedefinedField.Meta.model_fields["created_date"]
    assert changed_field.default is None
    assert changed_field.alias == "creation_date"
    assert any(x.name == "creation_date" for x in RedefinedField.Meta.table.columns)
    assert isinstance(
        RedefinedField.Meta.table.columns["creation_date"].type,
        sqlalchemy.sql.sqltypes.String,
    )


def test_model_subclassing_that_redefines_constraints_column_names():
    with pytest.raises(ModelDefinitionError):

        class WrongField2(DateFieldsModel):  # pragma: no cover
            class Meta(ormar.ModelMeta):
                tablename = "wrongs"
                metadata = metadata
                database = db

            id: int = ormar.Integer(primary_key=True)
            created_date: str = ormar.String(max_length=200)


def test_model_subclassing_non_abstract_raises_error():
    with pytest.raises(ModelDefinitionError):

        class WrongField2(DateFieldsModelNoSubclass):  # pragma: no cover
            class Meta(ormar.ModelMeta):
                tablename = "wrongs"
                metadata = metadata
                database = db

            id: int = ormar.Integer(primary_key=True)


def test_params_are_inherited():
    assert Category.Meta.metadata == metadata
    assert Category.Meta.database == db
    assert len(Category.Meta.constraints) == 2
    assert len(Category.Meta.property_fields) == 2


def round_date_to_seconds(
    date: datetime.datetime,
) -> datetime.datetime:  # pragma: no cover
    if date.microsecond >= 500000:
        date = date + datetime.timedelta(seconds=1)
    return date.replace(microsecond=0)


@pytest.mark.asyncio
async def test_fields_inherited_from_mixin():
    async with db:
        async with db.transaction(force_rollback=True):
            cat = await Category(
                name="Foo", code=123, created_by="Sam", updated_by="Max"
            ).save()
            sub = await Subject(name="Bar", category=cat).save()
            mixin_columns = ["created_date", "updated_date"]
            mixin_db_columns = ["creation_date", "modification_date"]
            mixin2_columns = ["created_by", "updated_by"]
            assert all(field in Category.Meta.model_fields for field in mixin_columns)
            assert cat.created_date is not None
            assert cat.updated_date is not None
            assert all(field in Subject.Meta.model_fields for field in mixin_columns)
            assert sub.created_date is not None
            assert sub.updated_date is not None

            assert all(field in Category.Meta.model_fields for field in mixin2_columns)
            assert all(
                field not in Subject.Meta.model_fields for field in mixin2_columns
            )

            inspector = sa.inspect(engine)
            assert "categories" in inspector.get_table_names()
            table_columns = [x.get("name") for x in inspector.get_columns("categories")]
            assert all(
                col in table_columns for col in mixin_db_columns
            )  # + mixin2_columns)

            assert "subjects" in inspector.get_table_names()
            table_columns = [x.get("name") for x in inspector.get_columns("subjects")]
            assert all(col in table_columns for col in mixin_db_columns)

            sub2 = (
                await Subject.objects.select_related("category")
                .order_by("-created_date")
                .exclude_fields("updated_date")
                .get()
            )
            assert round_date_to_seconds(sub2.created_date) == round_date_to_seconds(
                sub.created_date
            )
            assert sub2.category.updated_date is not None
            assert round_date_to_seconds(
                sub2.category.created_date
            ) == round_date_to_seconds(cat.created_date)
            assert sub2.updated_date is None
            assert sub2.category.created_by == "Sam"
            assert sub2.category.updated_by == cat.updated_by

            sub3 = (
                await Subject.objects.prefetch_related("category")
                .order_by("-created_date")
                .exclude_fields({"updated_date": ..., "category": {"updated_date"}})
                .get()
            )
            assert round_date_to_seconds(sub3.created_date) == round_date_to_seconds(
                sub.created_date
            )
            assert sub3.category.updated_date is None
            assert round_date_to_seconds(
                sub3.category.created_date
            ) == round_date_to_seconds(cat.created_date)
            assert sub3.updated_date is None
            assert sub3.category.created_by == "Sam"
            assert sub3.category.updated_by == cat.updated_by


@pytest.mark.asyncio
async def test_inheritance_with_relation():
    async with db:
        async with db.transaction(force_rollback=True):
            sam = await Person(name="Sam").save()
            joe = await Person(name="Joe").save()
            await Truck(
                name="Shelby wanna be", max_capacity=1400, owner=sam, co_owner=joe
            ).save()

            shelby = await Truck.objects.select_related(["owner", "co_owner"]).get()
            assert shelby.name == "Shelby wanna be"
            assert shelby.owner.name == "Sam"
            assert shelby.co_owner.name == "Joe"

            joe_check = await Person.objects.select_related("coowned_trucks").get(
                name="Joe"
            )
            assert joe_check.pk == joe.pk
            assert joe_check.coowned_trucks[0] == shelby
