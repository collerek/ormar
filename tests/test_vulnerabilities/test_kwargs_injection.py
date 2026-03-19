# type: ignore
"""
Tests that __pk_only__ and __excluded__ cannot be injected via kwargs.
"""

import pytest

import ormar
from ormar.exceptions import ModelError
from ormar.models import Model
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Item(Model):
    ormar_config = base_ormar_config.copy(tablename="security_items")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    secret: str = ormar.String(max_length=100, default="default_secret")


class Category(Model):
    ormar_config = base_ormar_config.copy(tablename="security_categories")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Product(Model):
    ormar_config = base_ormar_config.copy(tablename="security_products")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    category = ormar.ForeignKey(Category)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_pk_only_injection_rejected():
    """__pk_only__ in kwargs must not bypass validation."""
    with pytest.raises(ModelError, match="Unknown field '__pk_only__'"):
        Item(**{"__pk_only__": True, "id": 1, "name": "test"})


@pytest.mark.asyncio
async def test_pk_only_invalid_data_still_validated():
    """Even with __pk_only__=True in kwargs, validation still runs."""
    with pytest.raises(ModelError, match="Unknown field '__pk_only__'"):
        Item(**{"__pk_only__": True, "id": 1, "name": 123456})


@pytest.mark.asyncio
async def test_excluded_injection_ignored():
    """__excluded__ in kwargs must not nullify fields."""
    with pytest.raises(ModelError, match="Unknown field '__excluded__'"):
        Item(**{"__excluded__": {"secret"}, "id": 1, "name": "test"})


@pytest.mark.asyncio
async def test_create_with_pk_only_kwarg():
    """objects.create with __pk_only__ must not bypass validation."""
    with pytest.raises(ModelError, match="Unknown field '__pk_only__'"):
        await Item.objects.create(**{"__pk_only__": True, "id": 1, "name": "injected"})


@pytest.mark.asyncio
async def test_fk_relations_still_work():
    """Internal pk_only path via _internal_construct still works for FK."""
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            cat = await Category.objects.create(name="Electronics")
            prod = await Product.objects.create(name="Phone", category=cat)

            loaded = await Product.objects.select_related("category").get(id=prod.id)
            assert loaded.category.name == "Electronics"


@pytest.mark.asyncio
async def test_query_exclusions_still_work():
    """Internal excluded path via _internal_construct still works for queries."""
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            await Item.objects.create(name="widget", secret="hidden")
            loaded = await Item.objects.fields(["id", "name"]).get(name="widget")
            assert loaded.name == "widget"
            assert loaded.secret is None


@pytest.mark.asyncio
async def test_single_underscore_pk_only_not_a_threat():
    """_pk_only in kwargs is rejected as unknown field, not treated specially."""
    with pytest.raises(ModelError, match="Unknown field '_pk_only'"):
        Item(**{"_pk_only": True, "id": 1, "name": "test"})


@pytest.mark.asyncio
async def test_single_underscore_excluded_not_a_threat():
    """_excluded in kwargs is rejected as unknown field, not treated specially."""
    with pytest.raises(ModelError, match="Unknown field '_excluded'"):
        Item(**{"_excluded": {"secret"}, "id": 1, "name": "test"})


@pytest.mark.asyncio
async def test_internal_construct_pk_only():
    """_internal_construct with _pk_only=True skips validation."""
    instance = Item._internal_construct(_pk_only=True, id=42)
    assert instance.pk == 42
    assert instance.__pk_only__ is True


@pytest.mark.asyncio
async def test_internal_construct_excluded():
    """_internal_construct with _excluded nullifies fields."""
    instance = Item._internal_construct(
        _excluded={"secret"}, id=1, name="test", secret="value"
    )
    assert instance.secret is None
    assert instance.name == "test"
