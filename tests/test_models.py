import asyncio
from datetime import datetime
from typing import List

import databases
import pydantic
import pytest
import sqlalchemy
import uuid

import ormar
from ormar.exceptions import QueryDefinitionError, NoMatch
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class JsonSample(ormar.Model):
    class Meta:
        tablename = "jsons"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    test_json: ormar.JSON(nullable=True)


class UUIDSample(ormar.Model):
    class Meta:
        tablename = "uuids"
        metadata = metadata
        database = database

    id: ormar.UUID(primary_key=True, default=uuid.uuid4)
    test_text: ormar.Text()


class User(ormar.Model):
    class Meta:
        tablename = "users"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    name: ormar.String(max_length=100, default="")


class Product(ormar.Model):
    class Meta:
        tablename = "product"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    name: ormar.String(max_length=100)
    rating: ormar.Integer(minimum=1, maximum=5)
    in_stock: ormar.Boolean(default=False)
    last_delivery: ormar.Date(default=datetime.now)


country_name_choices = ("Canada", "Algeria", "United States")
country_taxed_choices = (True,)
country_country_code_choices = (-10, 1, 213, 1200)


class Country(ormar.Model):
    class Meta:
        tablename = "country"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    name: ormar.String(
        max_length=9, choices=country_name_choices, default="Canada",
    )
    taxed: ormar.Boolean(choices=country_taxed_choices, default=True)
    country_code: ormar.Integer(
        minimum=0, maximum=1000, choices=country_country_code_choices, default=1
    )


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="module")
async def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


def test_model_class():
    assert list(User.Meta.model_fields.keys()) == ["id", "name"]
    assert issubclass(User.Meta.model_fields["id"], pydantic.ConstrainedInt)
    assert User.Meta.model_fields["id"].primary_key is True
    assert issubclass(User.Meta.model_fields["name"], pydantic.ConstrainedStr)
    assert User.Meta.model_fields["name"].max_length == 100
    assert isinstance(User.Meta.table, sqlalchemy.Table)


def test_model_pk():
    user = User(pk=1)
    assert user.pk == 1
    assert user.id == 1


@pytest.mark.asyncio
async def test_json_column():
    async with database:
        async with database.transaction(force_rollback=True):
            await JsonSample.objects.create(test_json=dict(aa=12))
            await JsonSample.objects.create(test_json='{"aa": 12}')

            items = await JsonSample.objects.all()
            assert len(items) == 2
            assert items[0].test_json == dict(aa=12)
            assert items[1].test_json == dict(aa=12)


@pytest.mark.asyncio
async def test_uuid_column():
    async with database:
        async with database.transaction(force_rollback=True):
            u1 = await UUIDSample.objects.create(test_text="aa")
            u2 = await UUIDSample.objects.create(test_text="bb")

            items = await UUIDSample.objects.all()
            assert len(items) == 2

            assert isinstance(items[0].id, uuid.UUID)
            assert isinstance(items[1].id, uuid.UUID)

            assert items[0].id in (u1.id, u2.id)
            assert items[1].id in (u1.id, u2.id)

            assert items[0].id != items[1].id

            item = await UUIDSample.objects.filter(id=u1.id).get()
            assert item.id == u1.id


@pytest.mark.asyncio
async def test_model_crud():
    async with database:
        async with database.transaction(force_rollback=True):
            users = await User.objects.all()
            assert users == []

            user = await User.objects.create(name="Tom")
            users = await User.objects.all()
            assert user.name == "Tom"
            assert user.pk is not None
            assert users == [user]

            lookup = await User.objects.get()
            assert lookup == user

            await user.update(name="Jane")
            users = await User.objects.all()
            assert user.name == "Jane"
            assert user.pk is not None
            assert users == [user]

            await user.delete()
            users = await User.objects.all()
            assert users == []


@pytest.mark.asyncio
async def test_model_get():
    async with database:
        async with database.transaction(force_rollback=True):
            with pytest.raises(ormar.NoMatch):
                await User.objects.get()

            user = await User.objects.create(name="Tom")
            lookup = await User.objects.get()
            assert lookup == user

            user = await User.objects.create(name="Jane")
            with pytest.raises(ormar.MultipleMatches):
                await User.objects.get()

            same_user = await User.objects.get(pk=user.id)
            assert same_user.id == user.id
            assert same_user.pk == user.pk


@pytest.mark.asyncio
async def test_model_filter():
    async with database:
        async with database.transaction(force_rollback=True):
            await User.objects.create(name="Tom")
            await User.objects.create(name="Jane")
            await User.objects.create(name="Lucy")

            user = await User.objects.get(name="Lucy")
            assert user.name == "Lucy"

            with pytest.raises(ormar.NoMatch):
                await User.objects.get(name="Jim")

            await Product.objects.create(name="T-Shirt", rating=5, in_stock=True)
            await Product.objects.create(name="Dress", rating=4)
            await Product.objects.create(name="Coat", rating=3, in_stock=True)

            product = await Product.objects.get(name__iexact="t-shirt", rating=5)
            assert product.pk is not None
            assert product.name == "T-Shirt"
            assert product.rating == 5
            assert product.last_delivery == datetime.now().date()

            products = await Product.objects.all(rating__gte=2, in_stock=True)
            assert len(products) == 2

            products = await Product.objects.all(name__icontains="T")
            assert len(products) == 2

            products = await Product.objects.exclude(rating__gte=4).all()
            assert len(products) == 1

            products = await Product.objects.exclude(rating__gte=4, in_stock=True).all()
            assert len(products) == 2

            products = await Product.objects.exclude(in_stock=True).all()
            assert len(products) == 1

            products = await Product.objects.exclude(name__icontains="T").all()
            assert len(products) == 1

            # Test escaping % character from icontains, contains, and iexact
            await Product.objects.create(name="100%-Cotton", rating=3)
            await Product.objects.create(name="Cotton-100%-Egyptian", rating=3)
            await Product.objects.create(name="Cotton-100%", rating=3)
            products = Product.objects.filter(name__iexact="100%-cotton")
            assert await products.count() == 1

            products = Product.objects.filter(name__contains="%")
            assert await products.count() == 3

            products = Product.objects.filter(name__icontains="%")
            assert await products.count() == 3


@pytest.mark.asyncio
async def test_wrong_query_contains_model():
    async with database:
        with pytest.raises(QueryDefinitionError):
            product = Product(name="90%-Cotton", rating=2)
            await Product.objects.filter(name__contains=product).count()


@pytest.mark.asyncio
async def test_model_exists():
    async with database:
        async with database.transaction(force_rollback=True):
            await User.objects.create(name="Tom")
            assert await User.objects.filter(name="Tom").exists() is True
            assert await User.objects.filter(name="Jane").exists() is False


@pytest.mark.asyncio
async def test_model_count():
    async with database:
        async with database.transaction(force_rollback=True):
            await User.objects.create(name="Tom")
            await User.objects.create(name="Jane")
            await User.objects.create(name="Lucy")

            assert await User.objects.count() == 3
            assert await User.objects.filter(name__icontains="T").count() == 1


@pytest.mark.asyncio
async def test_model_limit():
    async with database:
        async with database.transaction(force_rollback=True):
            await User.objects.create(name="Tom")
            await User.objects.create(name="Jane")
            await User.objects.create(name="Lucy")

            assert len(await User.objects.limit(2).all()) == 2


@pytest.mark.asyncio
async def test_model_limit_with_filter():
    async with database:
        async with database.transaction(force_rollback=True):
            await User.objects.create(name="Tom")
            await User.objects.create(name="Tom")
            await User.objects.create(name="Tom")

            assert (
                len(await User.objects.limit(2).filter(name__iexact="Tom").all()) == 2
            )


@pytest.mark.asyncio
async def test_offset():
    async with database:
        async with database.transaction(force_rollback=True):
            await User.objects.create(name="Tom")
            await User.objects.create(name="Jane")

            users = await User.objects.offset(1).limit(1).all()
            assert users[0].name == "Jane"


@pytest.mark.asyncio
async def test_model_first():
    async with database:
        async with database.transaction(force_rollback=True):
            tom = await User.objects.create(name="Tom")
            jane = await User.objects.create(name="Jane")

            assert await User.objects.first() == tom
            assert await User.objects.first(name="Jane") == jane
            assert await User.objects.filter(name="Jane").first() == jane
            with pytest.raises(NoMatch):
                await User.objects.filter(name="Lucy").first()


def not_contains(a, b):
    return a not in b


def contains(a, b):
    return a in b


def check_choices(values: tuple, ops: List):
    ops_dict = {"in": contains, "out": not_contains}
    checks = (country_name_choices, country_taxed_choices, country_country_code_choices)
    assert all(
        [ops_dict[op](value, check) for value, op, check in zip(values, ops, checks)]
    )


@pytest.mark.asyncio
async def test_model_choices():
    """Test that choices work properly for various types of fields."""
    async with database:
        # Test valid choices.
        await asyncio.gather(
            Country.objects.create(name="Canada", taxed=True, country_code=1),
            Country.objects.create(name="Algeria", taxed=True, country_code=213),
            Country.objects.create(name="Algeria"),
        )

        with pytest.raises(ValueError):
            name, taxed, country_code = "Saudi Arabia", True, 1
            check_choices((name, taxed, country_code), ["out", "in", "in"])
            await Country.objects.create(
                name=name, taxed=taxed, country_code=country_code
            )

        with pytest.raises(ValueError):
            name, taxed, country_code = "Algeria", False, 1
            check_choices((name, taxed, country_code), ["in", "out", "in"])
            await Country.objects.create(
                name=name, taxed=taxed, country_code=country_code
            )

        with pytest.raises(ValueError):
            name, taxed, country_code = "Algeria", True, 967
            check_choices((name, taxed, country_code), ["in", "in", "out"])
            await Country.objects.create(
                name=name, taxed=taxed, country_code=country_code
            )

        with pytest.raises(ValueError):
            name, taxed, country_code = (
                "United States",
                True,
                1,
            )  # name is too long but is a valid choice
            check_choices((name, taxed, country_code), ["in", "in", "in"])
            await Country.objects.create(
                name=name, taxed=taxed, country_code=country_code
            )

        with pytest.raises(ValueError):
            name, taxed, country_code = (
                "Algeria",
                True,
                -10,
            )  # country code is too small but is a valid choice
            check_choices((name, taxed, country_code), ["in", "in", "in"])
            await Country.objects.create(
                name=name, taxed=taxed, country_code=country_code
            )

        with pytest.raises(ValueError):
            name, taxed, country_code = (
                "Algeria",
                True,
                1200,
            )  # country code is too large but is a valid choice
            check_choices((name, taxed, country_code), ["in", "in", "in"])
            await Country.objects.create(
                name=name, taxed=taxed, country_code=country_code
            )


@pytest.mark.asyncio
async def test_start_and_end_filters():
    async with database:
        async with database.transaction(force_rollback=True):
            await User.objects.create(name="Markos Uj")
            await User.objects.create(name="Maqua Bigo")
            await User.objects.create(name="maqo quidid")
            await User.objects.create(name="Louis Figo")
            await User.objects.create(name="Loordi Kami")
            await User.objects.create(name="Yuuki Sami")

            users = await User.objects.filter(name__startswith="Mar").all()
            assert len(users) == 1

            users = await User.objects.filter(name__istartswith="ma").all()
            assert len(users) == 3

            users = await User.objects.filter(name__istartswith="Maq").all()
            assert len(users) == 2

            users = await User.objects.filter(name__iendswith="AMI").all()
            assert len(users) == 2

            users = await User.objects.filter(name__endswith="Uj").all()
            assert len(users) == 1

            users = await User.objects.filter(name__endswith="igo").all()
            assert len(users) == 2
