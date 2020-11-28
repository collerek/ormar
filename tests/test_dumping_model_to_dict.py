from typing import Optional

import databases
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

metadata = sqlalchemy.MetaData()
database = databases.Database(DATABASE_URL, force_rollback=True)


class User(ormar.Model):
    class Meta:
        tablename: str = "users"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    email: str = ormar.String(max_length=255, nullable=False)
    password: str = ormar.String(max_length=255, nullable=True)
    first_name: str = ormar.String(max_length=255, nullable=False)


class Tier(ormar.Model):
    class Meta:
        tablename = "tiers"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Category(ormar.Model):
    class Meta:
        tablename = "categories"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    tier: Optional[Tier] = ormar.ForeignKey(Tier)


class Item(ormar.Model):
    class Meta:
        tablename = "items"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    category: Optional[Category] = ormar.ForeignKey(Category, nullable=True)
    created_by: Optional[User] = ormar.ForeignKey(User)


@pytest.fixture(autouse=True, scope="module")
def sample_data():
    user = User(email="test@test.com", password="ijacids7^*&", first_name="Anna")
    tier = Tier(name="Tier I")
    category1 = Category(name="Toys", tier=tier)
    category2 = Category(name="Weapons", tier=tier)
    item1 = Item(name="Teddy Bear", category=category1, created_by=user)
    item2 = Item(name="M16", category=category2, created_by=user)
    return item1, item2


def test_dumping_to_dict_no_exclusion(sample_data):
    item1, item2 = sample_data

    dict1 = item1.dict()
    assert dict1["name"] == "Teddy Bear"
    assert dict1["category"]["name"] == "Toys"
    assert dict1["category"]["tier"]["name"] == "Tier I"
    assert dict1["created_by"]["email"] == "test@test.com"

    dict2 = item2.dict()
    assert dict2["name"] == "M16"
    assert dict2["category"]["name"] == "Weapons"
    assert dict2["created_by"]["email"] == "test@test.com"


def test_dumping_to_dict_exclude_set(sample_data):
    item1, item2 = sample_data
    dict3 = item2.dict(exclude={"name"})
    assert "name" not in dict3
    assert dict3["category"]["name"] == "Weapons"
    assert dict3["created_by"]["email"] == "test@test.com"

    dict4 = item2.dict(exclude={"category"})
    assert dict4["name"] == "M16"
    assert "category" not in dict4
    assert dict4["created_by"]["email"] == "test@test.com"

    dict5 = item2.dict(exclude={"category", "name"})
    assert "name" not in dict5
    assert "category" not in dict5
    assert dict5["created_by"]["email"] == "test@test.com"


def test_dumping_to_dict_exclude_dict(sample_data):
    item1, item2 = sample_data
    dict6 = item2.dict(exclude={"category": {"name"}, "name": ...})
    assert "name" not in dict6
    assert "category" in dict6
    assert "name" not in dict6["category"]
    assert dict6["created_by"]["email"] == "test@test.com"


def test_dumping_to_dict_exclude_nested_dict(sample_data):
    item1, item2 = sample_data
    dict1 = item2.dict(exclude={"category": {"tier": {"name"}}, "name": ...})
    assert "name" not in dict1
    assert "category" in dict1
    assert dict1["category"]["name"] == "Weapons"
    assert dict1["created_by"]["email"] == "test@test.com"
    assert dict1["category"]["tier"].get("name") is None


def test_dumping_to_dict_exclude_and_include_nested_dict(sample_data):
    item1, item2 = sample_data
    dict1 = item2.dict(
        exclude={"category": {"tier": {"name"}}}, include={"name", "category"}
    )
    assert dict1.get("name") == "M16"
    assert "category" in dict1
    assert dict1["category"]["name"] == "Weapons"
    assert "created_by" not in dict1
    assert dict1["category"]["tier"].get("name") is None

    dict2 = item1.dict(
        exclude={"id": ...},
        include={"name": ..., "category": {"name": ..., "tier": {"id"}}},
    )
    assert dict2.get("name") == "Teddy Bear"
    assert dict2.get("id") is None  # models not saved
    assert dict2["category"]["name"] == "Toys"
    assert "created_by" not in dict1
    assert dict1["category"]["tier"].get("name") is None
    assert dict1["category"]["tier"]["id"] is None
