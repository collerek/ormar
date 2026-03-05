from typing import Optional

import pytest

import ormar
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Role(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=255, nullable=False)


class User(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    email: str = ormar.String(max_length=255, nullable=False)
    password: Optional[str] = ormar.String(max_length=255, nullable=True)
    first_name: str = ormar.String(max_length=255, nullable=False)
    roles: list[Role] = ormar.ManyToMany(Role)


class Tier(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Category(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="categories")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    tier: Optional[Tier] = ormar.ForeignKey(Tier)


class Item(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    category: Optional[Category] = ormar.ForeignKey(Category, nullable=True)
    created_by: Optional[User] = ormar.ForeignKey(User)


create_test_database = init_tests(base_ormar_config)


@pytest.fixture(autouse=True, scope="module")
def sample_data():
    role = Role(name="User", id=1)
    role2 = Role(name="Admin", id=2)
    user = User(
        id=1,
        email="test@test.com",
        password="ijacids7^*&",
        first_name="Anna",
        roles=[role, role2],
    )
    tier = Tier(id=1, name="Tier I")
    category1 = Category(id=1, name="Toys", tier=tier)
    category2 = Category(id=2, name="Weapons", tier=tier)
    item1 = Item(id=1, name="Teddy Bear", category=category1, created_by=user)
    item2 = Item(id=2, name="M16", category=category2, created_by=user)
    return item1, item2


def test_dumping_to_dict_no_exclusion(sample_data):
    item1, item2 = sample_data

    dict1 = item1.model_dump()
    assert dict1["name"] == "Teddy Bear"
    assert dict1["category"]["name"] == "Toys"
    assert dict1["category"]["tier"]["name"] == "Tier I"
    assert dict1["created_by"]["email"] == "test@test.com"

    dict2 = item2.model_dump()
    assert dict2["name"] == "M16"
    assert dict2["category"]["name"] == "Weapons"
    assert dict2["created_by"]["email"] == "test@test.com"


def test_dumping_to_dict_exclude_set(sample_data):
    item1, item2 = sample_data
    dict3 = item2.model_dump(exclude={"name"})
    assert "name" not in dict3
    assert dict3["category"]["name"] == "Weapons"
    assert dict3["created_by"]["email"] == "test@test.com"

    dict4 = item2.model_dump(exclude={"category"})
    assert dict4["name"] == "M16"
    assert "category" not in dict4
    assert dict4["created_by"]["email"] == "test@test.com"

    dict5 = item2.model_dump(exclude={"category", "name"})
    assert "name" not in dict5
    assert "category" not in dict5
    assert dict5["created_by"]["email"] == "test@test.com"


def test_dumping_to_dict_exclude_dict(sample_data):
    item1, item2 = sample_data
    dict6 = item2.model_dump(exclude={"category": {"name"}, "name": ...})
    assert "name" not in dict6
    assert "category" in dict6
    assert "name" not in dict6["category"]
    assert dict6["created_by"]["email"] == "test@test.com"


def test_dumping_to_dict_exclude_nested_dict(sample_data):
    item1, item2 = sample_data
    dict1 = item2.model_dump(exclude={"category": {"tier": {"name"}}, "name": ...})
    assert "name" not in dict1
    assert "category" in dict1
    assert dict1["category"]["name"] == "Weapons"
    assert dict1["created_by"]["email"] == "test@test.com"
    assert dict1["category"]["tier"].get("name") is None


def test_dumping_to_dict_exclude_and_include_nested_dict(sample_data):
    item1, item2 = sample_data
    dict1 = item2.model_dump(
        exclude={"category": {"tier": {"name"}}}, include={"name", "category"}
    )
    assert dict1.get("name") == "M16"
    assert "category" in dict1
    assert dict1["category"]["name"] == "Weapons"
    assert "created_by" not in dict1
    assert dict1["category"]["tier"].get("name") is None

    dict2 = item1.model_dump(
        exclude={"id": ...},
        include={"name": ..., "category": {"name": ..., "tier": {"id"}}},
    )
    assert dict2.get("name") == "Teddy Bear"
    assert dict2.get("id") is None  # models not saved
    assert dict2["category"]["name"] == "Toys"
    assert "created_by" not in dict1
    assert dict1["category"]["tier"].get("name") is None
    assert dict1["category"]["tier"]["id"] == 1


def test_dumping_dict_without_primary_keys(sample_data):
    item1, item2 = sample_data
    dict1 = item2.model_dump(exclude_primary_keys=True)
    assert dict1 == {
        "category": {"name": "Weapons", "tier": {"name": "Tier I"}},
        "created_by": {
            "email": "test@test.com",
            "first_name": "Anna",
            "password": "ijacids7^*&",
            "roles": [
                {"name": "User"},
                {"name": "Admin"},
            ],
        },
        "name": "M16",
    }
    dict2 = item1.model_dump(exclude_primary_keys=True)
    assert dict2 == {
        "category": {"name": "Toys", "tier": {"name": "Tier I"}},
        "created_by": {
            "email": "test@test.com",
            "first_name": "Anna",
            "password": "ijacids7^*&",
            "roles": [
                {"name": "User"},
                {"name": "Admin"},
            ],
        },
        "name": "Teddy Bear",
    }
