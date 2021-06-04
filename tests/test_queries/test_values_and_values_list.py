from typing import List, Optional

import databases
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    database = database
    metadata = metadata


class User(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Category(ormar.Model):
    class Meta(BaseMeta):
        tablename = "categories"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=40)
    sort_order: int = ormar.Integer(nullable=True)
    created_by: Optional[User] = ormar.ForeignKey(User)


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


@pytest.mark.asyncio
async def test_queryset_values():
    async with database:
        async with database.transaction(force_rollback=True):
            creator = await User(name="Anonymous").save()
            news = await Category(name="News", sort_order=0, created_by=creator).save()
            await Post(name="Ormar strikes again!", category=news).save()
            await Post(name="Why don't you use ormar yet?", category=news).save()
            await Post(name="Check this out, ormar now for free", category=news).save()

            posts = await Post.objects.values()
            assert posts == [
                {"id": 1, "name": "Ormar strikes again!", "category": 1},
                {"id": 2, "name": "Why don't you use ormar yet?", "category": 1},
                {"id": 3, "name": "Check this out, ormar now for free", "category": 1},
            ]

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
async def test_queryset_values_list():
    async with database:
        async with database.transaction(force_rollback=True):
            creator = await User(name="Anonymous").save()
            news = await Category(name="News", sort_order=0, created_by=creator).save()
            await Post(name="Ormar strikes again!", category=news).save()
            await Post(name="Why don't you use ormar yet?", category=news).save()
            await Post(name="Check this out, ormar now for free", category=news).save()

            posts = await Post.objects.values_list()
            assert posts == [
                (1, "Ormar strikes again!", 1),
                (2, "Why don't you use ormar yet?", 1),
                (3, "Check this out, ormar now for free", 1),
            ]

            posts = await Post.objects.select_related(
                "category__created_by"
            ).values_list()
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

            posts = await Post.objects.select_related(
                "category__created_by"
            ).values_list(["name", "category__name", "category__created_by__name"])
            assert posts == [
                ("Ormar strikes again!", "News", "Anonymous"),
                ("Why don't you use ormar yet?", "News", "Anonymous"),
                ("Check this out, ormar now for free", "News", "Anonymous"),
            ]
