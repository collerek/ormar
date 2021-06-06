import asyncio
from typing import List, Optional

import databases
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    database = database
    metadata = metadata


class User(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Role(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    users: List[User] = ormar.ManyToMany(User)


class Category(ormar.Model):
    class Meta(BaseMeta):
        tablename = "categories"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=40)
    sort_order: int = ormar.Integer(nullable=True)
    created_by: Optional[User] = ormar.ForeignKey(User, related_name="categories")


class Post(ormar.Model):
    class Meta(BaseMeta):
        tablename = "posts"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=200)
    category: Optional[Category] = ormar.ForeignKey(Category)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.yield_fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="module")
async def sample_data(event_loop, create_test_database):
    async with database:
        creator = await User(name="Anonymous").save()
        admin = await Role(name="admin").save()
        editor = await Role(name="editor").save()
        await creator.roles.add(admin)
        await creator.roles.add(editor)
        news = await Category(name="News", sort_order=0, created_by=creator).save()
        await Post(name="Ormar strikes again!", category=news).save()
        await Post(name="Why don't you use ormar yet?", category=news).save()
        await Post(name="Check this out, ormar now for free", category=news).save()


@pytest.mark.asyncio
async def test_simple_queryset_values():
    async with database:
        posts = await Post.objects.values()
        assert posts == [
            {"id": 1, "name": "Ormar strikes again!", "category": 1},
            {"id": 2, "name": "Why don't you use ormar yet?", "category": 1},
            {"id": 3, "name": "Check this out, ormar now for free", "category": 1},
        ]


@pytest.mark.asyncio
async def test_queryset_values_nested_relation():
    async with database:
        posts = await Post.objects.select_related("category__created_by").values()
        assert posts == [
            {
                "id": 1,
                "name": "Ormar strikes again!",
                "category": 1,
                "category__id": 1,
                "category__name": "News",
                "category__sort_order": 0,
                "category__created_by": 1,
                "category__created_by__id": 1,
                "category__created_by__name": "Anonymous",
            },
            {
                "category": 1,
                "id": 2,
                "name": "Why don't you use ormar yet?",
                "category__id": 1,
                "category__name": "News",
                "category__sort_order": 0,
                "category__created_by": 1,
                "category__created_by__id": 1,
                "category__created_by__name": "Anonymous",
            },
            {
                "id": 3,
                "name": "Check this out, ormar now for free",
                "category": 1,
                "category__id": 1,
                "category__name": "News",
                "category__sort_order": 0,
                "category__created_by": 1,
                "category__created_by__id": 1,
                "category__created_by__name": "Anonymous",
            },
        ]


@pytest.mark.asyncio
async def test_queryset_values_nested_relation_subset_of_fields():
    async with database:
        posts = await Post.objects.select_related("category__created_by").values(
            ["name", "category__name", "category__created_by__name"]
        )
        assert posts == [
            {
                "name": "Ormar strikes again!",
                "category__name": "News",
                "category__created_by__name": "Anonymous",
            },
            {
                "name": "Why don't you use ormar yet?",
                "category__name": "News",
                "category__created_by__name": "Anonymous",
            },
            {
                "name": "Check this out, ormar now for free",
                "category__name": "News",
                "category__created_by__name": "Anonymous",
            },
        ]


@pytest.mark.asyncio
async def test_queryset_simple_values_list():
    async with database:
        posts = await Post.objects.values_list()
        assert posts == [
            (1, "Ormar strikes again!", 1),
            (2, "Why don't you use ormar yet?", 1),
            (3, "Check this out, ormar now for free", 1),
        ]


@pytest.mark.asyncio
async def test_queryset_nested_relation_values_list():
    async with database:
        posts = await Post.objects.select_related("category__created_by").values_list()
        assert posts == [
            (1, "Ormar strikes again!", 1, 1, "News", 0, 1, 1, "Anonymous"),
            (2, "Why don't you use ormar yet?", 1, 1, "News", 0, 1, 1, "Anonymous"),
            (
                3,
                "Check this out, ormar now for free",
                1,
                1,
                "News",
                0,
                1,
                1,
                "Anonymous",
            ),
        ]


@pytest.mark.asyncio
async def test_queryset_nested_relation_subset_of_fields_values_list():
    async with database:
        posts = await Post.objects.select_related("category__created_by").values_list(
            ["name", "category__name", "category__created_by__name"]
        )
        assert posts == [
            ("Ormar strikes again!", "News", "Anonymous"),
            ("Why don't you use ormar yet?", "News", "Anonymous"),
            ("Check this out, ormar now for free", "News", "Anonymous"),
        ]


@pytest.mark.asyncio
async def test_m2m_values():
    async with database:
        user = await User.objects.select_related("roles").values()
        assert user == [
            {
                "id": 1,
                "name": "Anonymous",
                "roleuser__id": 1,
                "roleuser__role": 1,
                "roleuser__user": 1,
                "roles__id": 1,
                "roles__name": "admin",
            },
            {
                "id": 1,
                "name": "Anonymous",
                "roleuser__id": 2,
                "roleuser__role": 2,
                "roleuser__user": 1,
                "roles__id": 2,
                "roles__name": "editor",
            },
        ]


@pytest.mark.asyncio
async def test_nested_m2m_values():
    async with database:
        user = (
            await Role.objects.select_related("users__categories")
            .filter(name="admin")
            .values()
        )
        assert user == [
            {
                "id": 1,
                "name": "admin",
                "roleuser__id": 1,
                "roleuser__role": 1,
                "roleuser__user": 1,
                "users__id": 1,
                "users__name": "Anonymous",
                "users__categories__id": 1,
                "users__categories__name": "News",
                "users__categories__sort_order": 0,
                "users__categories__created_by": 1,
            }
        ]


@pytest.mark.asyncio
async def test_nested_m2m_values_subset_of_fields():
    async with database:
        user = (
            await Role.objects.select_related("users__categories")
            .filter(name="admin")
            .fields({"name": ..., "users": {"name": ..., "categories": {"name"}}})
            .exclude_fields("users__roleuser")
            .values()
        )
        assert user == [
            {
                "name": "admin",
                "users__name": "Anonymous",
                "users__categories__name": "News",
            }
        ]
